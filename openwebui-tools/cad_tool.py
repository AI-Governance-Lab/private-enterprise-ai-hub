"""
title: CAD Tools (DWG/DXF + XLSX)
author: private-enterprise-ai-hub
version: 0.3.0
description: >
    Tools to inspect an AutoCAD .dwg/.dxf file, extract surfaces (areas) into
    JSON or a downloadable XLSX/CSV file, and reconcile the drawing against
    an existing XLSX reference table. Talks to the cad-service container on
    the internal private-ai-net network.

    Generated XLSX/CSV files are stored in Open WebUI's file store and
    returned as clickable download links (Markdown), NOT base64 blobs.

    All tools degrade gracefully if the cad-service is down: they return a
    clear error message instead of raising, so the rest of the chat works.

How the user uploads files:
    1. Attach a .dwg / .dxf (and optionally an .xlsx) to the chat message.
    2. The model calls one of the tools below with NO file arguments — the
       __files__ kwarg is injected automatically by Open WebUI.
    3. Each tool picks the right file(s) by extension from __files__ and
       posts the raw bytes to cad-service.

Import in Open WebUI: Workspace -> Tools -> Import from file -> upload this
Python file, then enable it for the models you want.

Ask the user for layer patterns and column names — do NOT hard-code them.
Typical Romanian expropriation drawings use layers like S_EXPROPRIERE_*,
PARCELE_*, ROAD_ROW_*; XLSX columns like `Nr_parcela`, `Suprafata_masurata_mp`.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

CAD_SERVICE_URL = os.getenv("CAD_SERVICE_URL", "http://cad-service:8090")
UPLOADS_DIR = os.getenv("OPENWEBUI_UPLOADS_DIR", "/app/backend/data/uploads")
WEBUI_DB = os.getenv("OPENWEBUI_DB", "/app/backend/data/webui.db")
HTTP_TIMEOUT = float(os.getenv("CAD_HTTP_TIMEOUT_S", "300"))

CAD_EXTS = (".dwg", ".dxf")
XLSX_EXTS = (".xlsx", ".xlsm")

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MIME_CSV = "text/csv; charset=utf-8"


def _service_error(action: str, err: Exception) -> str:
    """Return a user-visible error blob instead of raising, so the chat continues."""
    return json.dumps({
        "error": "cad_service_unavailable",
        "action": action,
        "detail": f"{type(err).__name__}: {err}",
        "hint": (
            "The CAD service is not responding. The rest of the chat still works. "
            "Check: `docker ps | grep cad-service` and `docker logs cad-service`."
        ),
    }, ensure_ascii=False)


def _pick_file(files: list[dict] | None, exts: tuple[str, ...]) -> dict | None:
    """From the __files__ list, return the last-attached file whose name
    ends with one of the given extensions (last-attached wins for reruns)."""
    if not files:
        return None
    for f in reversed(files):
        name = (f.get("name") or f.get("filename") or "").lower()
        if name.endswith(exts):
            return f
    return None


def _resolve_local_path(f: dict) -> Path | None:
    """Open WebUI stores uploads as `{id}_{name}` under UPLOADS_DIR. Search
    the directory in case a hosted deployment renamed the path scheme."""
    file_id = f.get("id") or f.get("file_id")
    name = f.get("name") or f.get("filename") or ""
    base = Path(UPLOADS_DIR)
    if file_id:
        primary = base / f"{file_id}_{name}"
        if primary.exists():
            return primary
        for p in base.glob(f"{file_id}*"):
            return p
    if name:
        for p in base.glob(f"*_{name}"):
            return p
    return None


def _no_file_error(action: str, exts: tuple[str, ...], files: list[dict] | None) -> str:
    return json.dumps({
        "error": "no_matching_file_attached",
        "action": action,
        "expected_extensions": list(exts),
        "attached_now": [f.get("name") for f in (files or [])],
        "hint": (
            f"Ask the user to attach a file ending in {', '.join(exts)} to this chat message."
        ),
    }, ensure_ascii=False)


def _file_not_on_disk(action: str, f: dict) -> str:
    return json.dumps({
        "error": "file_not_on_disk",
        "action": action,
        "file_id": f.get("id"),
        "file_name": f.get("name"),
        "uploads_dir": UPLOADS_DIR,
        "hint": (
            "The file was referenced in the chat but is not readable at the "
            f"expected path under {UPLOADS_DIR}. Ask the user to re-upload it."
        ),
    }, ensure_ascii=False)


def _register_generated_file(
    content: bytes, filename: str, mime: str, user_id: str,
) -> tuple[str, str] | None:
    """Save a tool-generated blob into Open WebUI's file store so it becomes
    a clickable download in chat.

    Returns (file_id, path) or None if registration failed.
    """
    try:
        file_id = str(uuid.uuid4())
        safe_name = Path(filename).name
        path = Path(UPLOADS_DIR) / f"{file_id}_{safe_name}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

        db = sqlite3.connect(WEBUI_DB, timeout=10.0)
        try:
            now = int(time.time())
            file_hash = hashlib.sha256(content).hexdigest()
            meta = json.dumps({
                "name": safe_name,
                "content_type": mime,
                "size": len(content),
                "file_hash": file_hash,
                "data": {},
            })
            data = json.dumps({"status": "generated", "source": "cad-tool"})
            db.execute(
                "INSERT INTO file (id, user_id, filename, meta, created_at, "
                "hash, data, updated_at, path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (file_id, user_id, safe_name, meta, now, file_hash, data, now, str(path)),
            )
            db.commit()
        finally:
            db.close()
        return file_id, str(path)
    except Exception:  # noqa: BLE001
        return None


async def _post(endpoint: str, files: dict[str, tuple], data: dict[str, Any] | None = None) -> httpx.Response:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as c:
        return await c.post(f"{CAD_SERVICE_URL}{endpoint}", files=files, data=data or {})


class Tools:
    """Open WebUI tool container. Each public async method becomes a callable tool.

    Every tool takes an implicit `__files__` list injected by Open WebUI when
    the user attaches files to the message. Tools locate their own inputs from
    this list by extension — the model does NOT pass file ids or URLs.
    """

    def __init__(self) -> None:
        self.citation = True

    async def cad_health(self) -> str:
        """Check whether the CAD extraction service is up. Call this first if
        you suspect a problem. Returns JSON with status and converter version.
        """
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{CAD_SERVICE_URL}/health")
                return r.text
        except Exception as e:  # noqa: BLE001
            return _service_error("health", e)

    async def cad_introspect(self, __files__: list[dict] | None = None) -> str:
        """Inspect the most recently attached DWG/DXF and return the list of
        layers with entity counts and block attribute keys. Use this FIRST to
        ask the user which layers hold the parcels and which block attribute
        holds the parcel id.
        """
        f = _pick_file(__files__, CAD_EXTS)
        if f is None:
            return _no_file_error("introspect", CAD_EXTS, __files__)
        path = _resolve_local_path(f)
        if path is None:
            return _file_not_on_disk("introspect", f)
        try:
            with path.open("rb") as fh:
                content = fh.read()
            r = await _post("/introspect", files={"file": (path.name, content)})
            r.raise_for_status()
            return r.text
        except Exception as e:  # noqa: BLE001
            return _service_error("introspect", e)

    async def cad_extract(
        self,
        layers: str = "*",
        source_types: str = "block_attr,hatch,lwpolyline_closed,polyline_closed",
        unit: str = "m2",
        __files__: list[dict] | None = None,
    ) -> str:
        """Extract closed-area entities from the attached DWG/DXF, filtered by
        layer patterns. Ask the user for layer patterns first via cad_introspect.

        :param layers: comma-separated glob patterns (e.g. 'S_EXPROPRIERE_*,PARCELE_*')
        :param source_types: which entity kinds to pick (block_attr,hatch,lwpolyline_closed,polyline_closed)
        :param unit: output area unit — one of m2, ha, km2
        """
        f = _pick_file(__files__, CAD_EXTS)
        if f is None:
            return _no_file_error("extract", CAD_EXTS, __files__)
        path = _resolve_local_path(f)
        if path is None:
            return _file_not_on_disk("extract", f)
        try:
            with path.open("rb") as fh:
                content = fh.read()
            r = await _post("/extract",
                            files={"file": (path.name, content)},
                            data={"layers": layers, "source_types": source_types, "unit": unit})
            r.raise_for_status()
            return r.text
        except Exception as e:  # noqa: BLE001
            return _service_error("extract", e)

    async def cad_export(
        self,
        layers: str = "*",
        source_types: str = "block_attr,hatch,lwpolyline_closed,polyline_closed",
        unit: str = "m2",
        sheet_name: str = "Suprafete",
        format: str = "xlsx",
        __files__: list[dict] | None = None,
        __user__: dict | None = None,
    ) -> str:
        """Extract areas from the attached DWG/DXF and register a downloadable
        XLSX or CSV file in the chat. Returns a Markdown link that the user
        can click to download.

        :param layers: comma-separated glob patterns
        :param source_types: which entity kinds to pick
        :param unit: m2 | ha | km2
        :param sheet_name: XLSX sheet name (ignored for CSV)
        :param format: 'xlsx' (default) or 'csv'
        """
        fmt = (format or "xlsx").lower()
        if fmt not in ("xlsx", "csv"):
            return json.dumps({"error": "bad_format", "hint": "format must be 'xlsx' or 'csv'"})

        f = _pick_file(__files__, CAD_EXTS)
        if f is None:
            return _no_file_error("export", CAD_EXTS, __files__)
        path = _resolve_local_path(f)
        if path is None:
            return _file_not_on_disk("export", f)
        try:
            with path.open("rb") as fh:
                content = fh.read()
            r = await _post("/export-excel",
                            files={"file": (path.name, content)},
                            data={"layers": layers, "source_types": source_types,
                                  "unit": unit, "sheet_name": sheet_name, "format": fmt})
            r.raise_for_status()
            blob = r.content

            filename = f"{Path(path.name).stem}_areas_{unit}.{fmt}"
            cd = r.headers.get("content-disposition", "")
            if 'filename="' in cd:
                filename = cd.split('filename="', 1)[1].split('"', 1)[0]

            mime = MIME_CSV if fmt == "csv" else MIME_XLSX
            user_id = (__user__ or {}).get("id", "")
            reg = _register_generated_file(blob, filename, mime, user_id)
            if reg is None:
                import base64
                return json.dumps({
                    "warning": "file_registration_failed_fallback_base64",
                    "filename": filename,
                    "size_bytes": len(blob),
                    "content_base64": base64.b64encode(blob).decode("ascii"),
                    "media_type": mime,
                }, ensure_ascii=False)

            file_id, disk_path = reg
            return json.dumps({
                "ok": True,
                "filename": filename,
                "size_bytes": len(blob),
                "media_type": mime,
                "file_id": file_id,
                "download_url": f"/api/v1/files/{file_id}/content",
                "markdown_link": f"[⬇️ {filename}](/api/v1/files/{file_id}/content)",
                "hint": (
                    "Present the `markdown_link` verbatim to the user as a "
                    "clickable download; do NOT reformat it or add extra text "
                    "inside the brackets."
                ),
            }, ensure_ascii=False)
        except Exception as e:  # noqa: BLE001
            return _service_error("export", e)

    async def cad_to_excel(
        self,
        layers: str = "*",
        source_types: str = "block_attr,hatch,lwpolyline_closed,polyline_closed",
        unit: str = "m2",
        sheet_name: str = "Suprafete",
        __files__: list[dict] | None = None,
        __user__: dict | None = None,
    ) -> str:
        """Convenience wrapper: extract areas from the attached DWG/DXF and
        return a Markdown download link to an XLSX file. Use when the user
        asks for Excel specifically."""
        return await self.cad_export(
            layers=layers, source_types=source_types, unit=unit,
            sheet_name=sheet_name, format="xlsx",
            __files__=__files__, __user__=__user__,
        )

    async def cad_to_csv(
        self,
        layers: str = "*",
        source_types: str = "block_attr,hatch,lwpolyline_closed,polyline_closed",
        unit: str = "m2",
        __files__: list[dict] | None = None,
        __user__: dict | None = None,
    ) -> str:
        """Convenience wrapper: extract areas from the attached DWG/DXF and
        return a Markdown download link to a CSV file. Use when the user
        asks for CSV specifically."""
        return await self.cad_export(
            layers=layers, source_types=source_types, unit=unit,
            format="csv",
            __files__=__files__, __user__=__user__,
        )

    async def cad_reconcile(
        self,
        xlsx_key_column: str,
        xlsx_area_column: str,
        dwg_key_attribute: str = "",
        layers: str = "*",
        source_types: str = "block_attr,hatch,lwpolyline_closed,polyline_closed",
        unit: str = "m2",
        xlsx_sheet: str = "",
        tolerance_pct: float = 0.5,
        tolerance_abs: float = 0.01,
        __files__: list[dict] | None = None,
    ) -> str:
        """Reconcile the attached DWG/DXF against the attached XLSX reference
        table. Both files must be attached to the same message. Ask the user
        which XLSX columns to use before calling this. Typical:
        xlsx_key_column='Nr_parcela', xlsx_area_column='Suprafata_masurata_mp',
        dwg_key_attribute='NR_PARCELA'.

        :param xlsx_key_column: header name in XLSX that identifies the parcel
        :param xlsx_area_column: header name in XLSX that holds the area
        :param dwg_key_attribute: block attribute tag identifying the parcel in DWG
        :param layers: comma-separated glob patterns
        :param source_types: which entity kinds to pick
        :param unit: m2 | ha | km2 (must match the XLSX area column unit)
        :param xlsx_sheet: sheet name; blank means the active sheet
        :param tolerance_pct: relative tolerance in percent (default 0.5%)
        :param tolerance_abs: absolute tolerance in `unit` (default 0.01)
        """
        dwg = _pick_file(__files__, CAD_EXTS)
        xlsx = _pick_file(__files__, XLSX_EXTS)
        missing = []
        if dwg is None:
            missing.append("a .dwg or .dxf drawing")
        if xlsx is None:
            missing.append("an .xlsx reference table")
        if missing:
            return json.dumps({
                "error": "missing_files",
                "action": "reconcile",
                "need": missing,
                "attached_now": [f.get("name") for f in (__files__ or [])],
                "hint": "Ask the user to attach both files to the same chat message.",
            }, ensure_ascii=False)
        dwg_path = _resolve_local_path(dwg)
        xlsx_path = _resolve_local_path(xlsx)
        if dwg_path is None:
            return _file_not_on_disk("reconcile", dwg)
        if xlsx_path is None:
            return _file_not_on_disk("reconcile", xlsx)
        try:
            with dwg_path.open("rb") as fd, xlsx_path.open("rb") as fx:
                files = {
                    "dwg":  (dwg_path.name,  fd.read()),
                    "xlsx": (xlsx_path.name, fx.read()),
                }
            r = await _post("/reconcile", files=files, data={
                "layers": layers, "source_types": source_types, "unit": unit,
                "xlsx_sheet": xlsx_sheet,
                "xlsx_key_column": xlsx_key_column,
                "xlsx_area_column": xlsx_area_column,
                "dwg_key_attribute": dwg_key_attribute,
                "tolerance_pct": tolerance_pct,
                "tolerance_abs": tolerance_abs,
            })
            r.raise_for_status()
            return r.text
        except Exception as e:  # noqa: BLE001
            return _service_error("reconcile", e)

