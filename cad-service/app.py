"""CAD service — DWG/DXF area extraction and XLSX reconciliation.

Endpoints:
  GET  /health
  POST /introspect     -> discover layers, entity counts, block attribute keys
  POST /extract        -> extract closed areas from selected layers
  POST /export-excel   -> extract + return an XLSX with areas + totals
  POST /reconcile      -> compare a DWG's areas against an XLSX reference

The service converts DWG -> DXF with `dwg2dxf` (libredwg-tools) and then
parses geometry with `ezdxf`. Unit conversion is derived from $INSUNITS
in the DXF header when present; callers may override with a scale factor.
"""
from __future__ import annotations

import csv
import io
import logging
import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf import path as dxf_path
from ezdxf.document import Drawing
from ezdxf.entities import DXFEntity
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from openpyxl import Workbook, load_workbook
from shapely.geometry import Polygon

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("cad-service")

app = FastAPI(title="CAD Service", version="0.1.0",
              description="DWG/DXF area extraction & XLSX reconciliation for expropriation workflows.")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "500"))
DWG2DXF = os.getenv("DWG2DXF_BIN", "dwg2dxf")
CONVERT_TIMEOUT_S = int(os.getenv("CONVERT_TIMEOUT_S", "300"))

# INSUNITS code -> meters per drawing unit (only common surveying/architectural values)
INSUNITS_TO_METERS: dict[int, float] = {
    0: 1.0,          # unspecified; assume meters (common for cadastre)
    1: 0.0254,       # inches
    2: 0.3048,       # feet
    4: 0.001,        # millimeters
    5: 0.01,         # centimeters
    6: 1.0,          # meters
    7: 1000.0,       # kilometers
    14: 0.1,         # decimeters
    15: 10.0,        # dekameters
    16: 100.0,       # hectometers
}
UNIT_LABEL: dict[int, str] = {
    0: "unspecified", 1: "in", 2: "ft", 4: "mm", 5: "cm",
    6: "m", 7: "km", 14: "dm", 15: "dam", 16: "hm",
}

OUTPUT_UNITS = {"m2": 1.0, "ha": 1e-4, "km2": 1e-6}


# --------------------------- helpers ---------------------------

def _convert_dwg_to_dxf(src: Path, dst: Path) -> None:
    """Convert a DWG file to DXF using libredwg's dwg2dxf."""
    try:
        proc = subprocess.run(
            [DWG2DXF, "-y", "-o", str(dst), str(src)],
            capture_output=True, text=True, timeout=CONVERT_TIMEOUT_S,
        )
    except FileNotFoundError as e:
        raise HTTPException(500, f"DWG converter '{DWG2DXF}' not installed: {e}")
    except subprocess.TimeoutExpired:
        raise HTTPException(504, f"DWG->DXF conversion timed out after {CONVERT_TIMEOUT_S}s")
    if not dst.exists() or dst.stat().st_size == 0:
        raise HTTPException(500, f"DWG->DXF conversion produced no output. stderr={proc.stderr[:400]}")


def _load_dxf(src: Path) -> Drawing:
    """Load a DXF file, converting from DWG first if needed."""
    ext = src.suffix.lower()
    if ext == ".dxf":
        return ezdxf.readfile(str(src))
    if ext == ".dwg":
        with tempfile.TemporaryDirectory() as td:
            dxf_path = Path(td) / "converted.dxf"
            _convert_dwg_to_dxf(src, dxf_path)
            return ezdxf.readfile(str(dxf_path))
    raise HTTPException(400, f"Unsupported extension: {ext} (expected .dwg or .dxf)")


async def _save_upload(file: UploadFile, dst_dir: Path) -> Path:
    """Persist an uploaded file to a temp path, enforcing size limits."""
    safe_name = Path(file.filename or "").name
    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(400, "Missing or invalid filename")
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    dst = dst_dir / safe_name
    written = 0
    with dst.open("wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                raise HTTPException(413, f"File too large (> {MAX_UPLOAD_MB} MB)")
            f.write(chunk)
    return dst


def _insunits(doc: Drawing) -> tuple[int, float, str]:
    """Return (insunits_code, meters_per_unit, unit_label)."""
    code = int(doc.header.get("$INSUNITS", 0))
    return code, INSUNITS_TO_METERS.get(code, 1.0), UNIT_LABEL.get(code, f"code_{code}")


def _shoelace(points: list[tuple[float, float]]) -> float:
    """Absolute polygon area via the shoelace formula. Requires >=3 vertices."""
    n = len(points)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _perimeter(points: list[tuple[float, float]]) -> float:
    n = len(points)
    if n < 2:
        return 0.0
    total = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        total += math.hypot(x2 - x1, y2 - y1)
    return total


def _centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    if not points:
        return (0.0, 0.0)
    return (sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points))


def _lwpolyline_points(e: DXFEntity) -> list[tuple[float, float]]:
    return [(float(p[0]), float(p[1])) for p in e.get_points("xy")]


def _polyline_points(e: DXFEntity) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for v in e.vertices:  # type: ignore[attr-defined]
        loc = v.dxf.location
        pts.append((float(loc.x), float(loc.y)))
    return pts


def _hatch_boundary_points(hatch: DXFEntity) -> list[tuple[float, float]]:
    """Concatenate all polyline-boundary vertices of a HATCH into a single polygon."""
    pts: list[tuple[float, float]] = []
    for path in getattr(hatch, "paths", []):
        path_type = path.PATH_TYPE if hasattr(path, "PATH_TYPE") else ""
        if path_type == "PolylinePath":
            for v in path.vertices:
                pts.append((float(v[0]), float(v[1])))
        elif path_type == "EdgePath":
            for edge in path.edges:
                # Only line edges are handled; arcs/splines are approximated by endpoints.
                start = getattr(edge, "start", None)
                if start is not None:
                    pts.append((float(start[0]), float(start[1])))
    return pts


def _geometry_metrics_from_entity(e: DXFEntity, t: str) -> tuple[float, float, float, float] | None:
    """Compute (area, perimeter, centroid_x, centroid_y) in drawing units.

    Uses ezdxf.path + shapely to accurately flatten curved segments (bulges,
    arcs, splines) and respect multi-loop HATCH islands/holes via symmetric
    difference. Falls back to vertex shoelace if path/polygon construction fails.
    """
    try:
        if t == "HATCH":
            loop_polys: list[Polygon] = []
            for p in dxf_path.from_hatch(e):  # type: ignore[arg-type]
                pts = [(float(v.x), float(v.y)) for v in p.flattening(distance=0.01)]
                if len(pts) >= 3:
                    poly = Polygon(pts)
                    if not poly.is_valid:
                        poly = poly.buffer(0)
                    if not poly.is_empty and poly.area > 0:
                        loop_polys.append(poly)
            if loop_polys:
                loop_polys.sort(key=lambda g: g.area, reverse=True)
                combined = loop_polys[0]
                for poly in loop_polys[1:]:
                    combined = combined.symmetric_difference(poly)
                if not combined.is_empty and combined.area > 0:
                    c = combined.centroid
                    return float(combined.area), float(combined.length), float(c.x), float(c.y)
        elif t in ("LWPOLYLINE", "POLYLINE"):
            p = dxf_path.make_path(e)
            pts = [(float(v.x), float(v.y)) for v in p.flattening(distance=0.01)]
            if len(pts) >= 3:
                poly = Polygon(pts)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                if not poly.is_empty and poly.area > 0:
                    c = poly.centroid
                    return float(poly.area), float(poly.length), float(c.x), float(c.y)
    except Exception:  # noqa: BLE001
        pass

    # Fallback to classic vertex shoelace
    if t == "HATCH":
        pts = _hatch_boundary_points(e)
    elif t == "LWPOLYLINE":
        pts = _lwpolyline_points(e)
    elif t == "POLYLINE":
        pts = _polyline_points(e)
    else:
        return None

    if len(pts) < 3:
        return None
    cx, cy = _centroid(pts)
    return _shoelace(pts), _perimeter(pts), cx, cy


def _layer_match(layer_name: str, patterns: list[str]) -> bool:
    return any(fnmatch(layer_name, p) or fnmatch(layer_name.upper(), p.upper()) for p in patterns)


def _split_patterns(raw: str) -> list[str]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or ["*"]


@dataclass
class ExtractedArea:
    layer: str
    source_type: str          # "block_attr" | "hatch" | "lwpolyline_closed" | "polyline_closed"
    area_m2: float
    perimeter_m: float
    centroid_x: float
    centroid_y: float
    attributes: dict[str, str]

    def to_row(self, out_unit: str) -> dict[str, Any]:
        factor = OUTPUT_UNITS[out_unit]
        return {
            "layer": self.layer,
            "source_type": self.source_type,
            f"area_{out_unit}": round(self.area_m2 * factor, 6),
            "perimeter_m": round(self.perimeter_m, 3),
            "centroid_x": round(self.centroid_x, 3),
            "centroid_y": round(self.centroid_y, 3),
            **self.attributes,
        }


def _extract_from_doc(doc: Drawing, layer_patterns: list[str],
                      source_types: list[str]) -> list[ExtractedArea]:
    """Walk modelspace and pull closed geometry from matching layers.

    Blocks with the sought attribute keys are treated as the authoritative
    source when present; hatch and closed polylines are fallbacks.
    """
    _, meters_per_unit, _ = _insunits(doc)
    unit2 = meters_per_unit * meters_per_unit
    msp = doc.modelspace()
    out: list[ExtractedArea] = []

    for e in msp:
        layer = e.dxf.layer
        if not _layer_match(layer, layer_patterns):
            continue
        t = e.dxftype()

        if t == "INSERT" and "block_attr" in source_types:
            attrs = {a.dxf.tag: str(a.dxf.text) for a in e.attribs}  # type: ignore[attr-defined]
            if not attrs:
                continue
            area_m2 = 0.0
            for key in ("AREA", "SUPRAFATA", "SUPRAFATA_MP", "AREA_MP", "SUPR"):
                if key in attrs:
                    try:
                        area_m2 = float(str(attrs[key]).replace(",", "."))
                        break
                    except ValueError:
                        continue
            loc = e.dxf.insert
            out.append(ExtractedArea(
                layer=layer, source_type="block_attr",
                area_m2=area_m2, perimeter_m=0.0,
                centroid_x=float(loc.x) * meters_per_unit,
                centroid_y=float(loc.y) * meters_per_unit,
                attributes=attrs,
            ))
            continue

        if t == "HATCH" and "hatch" in source_types:
            metrics = _geometry_metrics_from_entity(e, "HATCH")
            if metrics is None:
                continue
            raw_area, raw_perim, cx, cy = metrics
            out.append(ExtractedArea(
                layer=layer, source_type="hatch",
                area_m2=raw_area * unit2,
                perimeter_m=raw_perim * meters_per_unit,
                centroid_x=cx * meters_per_unit,
                centroid_y=cy * meters_per_unit,
                attributes={},
            ))
            continue

        if t == "LWPOLYLINE" and getattr(e, "closed", False) and "lwpolyline_closed" in source_types:
            metrics = _geometry_metrics_from_entity(e, "LWPOLYLINE")
            if metrics is None:
                continue
            raw_area, raw_perim, cx, cy = metrics
            out.append(ExtractedArea(
                layer=layer, source_type="lwpolyline_closed",
                area_m2=raw_area * unit2,
                perimeter_m=raw_perim * meters_per_unit,
                centroid_x=cx * meters_per_unit,
                centroid_y=cy * meters_per_unit,
                attributes={},
            ))
            continue

        if t == "POLYLINE" and getattr(e, "is_closed", False) and "polyline_closed" in source_types:
            metrics = _geometry_metrics_from_entity(e, "POLYLINE")
            if metrics is None:
                continue
            raw_area, raw_perim, cx, cy = metrics
            out.append(ExtractedArea(
                layer=layer, source_type="polyline_closed",
                area_m2=raw_area * unit2,
                perimeter_m=raw_perim * meters_per_unit,
                centroid_x=cx * meters_per_unit,
                centroid_y=cy * meters_per_unit,
                attributes={},
            ))

    return out


# --------------------------- endpoints ---------------------------

@app.get("/health")
def health() -> dict[str, Any]:
    try:
        proc = subprocess.run([DWG2DXF, "--version"], capture_output=True, text=True, timeout=5)
        converter_ok = proc.returncode == 0
        converter_version = (proc.stdout or proc.stderr).strip().splitlines()[0] if converter_ok else ""
    except Exception as e:  # noqa: BLE001
        converter_ok = False
        converter_version = f"error: {e}"
    return {
        "status": "ok" if converter_ok else "degraded",
        "converter": DWG2DXF,
        "converter_ok": converter_ok,
        "converter_version": converter_version,
        "ezdxf_version": ezdxf.__version__,
        "max_upload_mb": MAX_UPLOAD_MB,
    }


@app.post("/introspect")
async def introspect(file: UploadFile = File(...)) -> JSONResponse:
    """Return layer inventory and block attribute keys — used by the LLM to
    ask the user which layers and columns are relevant before extraction."""
    with tempfile.TemporaryDirectory() as td:
        src = await _save_upload(file, Path(td))
        doc = _load_dxf(src)
        code, mpu, label = _insunits(doc)
        msp = doc.modelspace()
        layer_stats: dict[str, dict[str, int]] = {}
        block_attrs: dict[str, int] = {}
        for e in msp:
            layer = e.dxf.layer
            s = layer_stats.setdefault(layer, {
                "total": 0, "hatch": 0,
                "lwpolyline_closed": 0, "lwpolyline_open": 0,
                "polyline_closed": 0, "polyline_open": 0,
                "insert": 0, "text": 0, "mtext": 0, "line": 0,
            })
            s["total"] += 1
            t = e.dxftype()
            if t == "HATCH":
                s["hatch"] += 1
            elif t == "LWPOLYLINE":
                s["lwpolyline_closed" if getattr(e, "closed", False) else "lwpolyline_open"] += 1
            elif t == "POLYLINE":
                s["polyline_closed" if getattr(e, "is_closed", False) else "polyline_open"] += 1
            elif t == "INSERT":
                s["insert"] += 1
                for a in e.attribs:  # type: ignore[attr-defined]
                    block_attrs[a.dxf.tag] = block_attrs.get(a.dxf.tag, 0) + 1
            elif t == "TEXT":
                s["text"] += 1
            elif t == "MTEXT":
                s["mtext"] += 1
            elif t == "LINE":
                s["line"] += 1

        return JSONResponse({
            "filename": file.filename,
            "dxf_version": doc.dxfversion,
            "insunits_code": code,
            "meters_per_unit": mpu,
            "unit_label": label,
            "layer_count": len(layer_stats),
            "layers": [{"name": name, **stats} for name, stats in sorted(layer_stats.items())],
            "block_attribute_keys": [{"tag": k, "count": v} for k, v in sorted(block_attrs.items(), key=lambda kv: -kv[1])],
            "message": (
                "Ask the user which layers hold the surfaces of interest (glob patterns like "
                "'S_*' or 'PARCELA_*' accepted). If block_attribute_keys is non-empty, ask which "
                "tag identifies the parcel ID and which holds the area."
            ),
        })


@app.post("/extract")
async def extract(
    file: UploadFile = File(...),
    layers: str = Form("*"),
    source_types: str = Form("block_attr,hatch,lwpolyline_closed,polyline_closed"),
    unit: str = Form("m2"),
) -> JSONResponse:
    """Extract closed-area entities from selected layers."""
    if unit not in OUTPUT_UNITS:
        raise HTTPException(400, f"unit must be one of {list(OUTPUT_UNITS)}")
    patterns = _split_patterns(layers)
    src_types = _split_patterns(source_types)

    with tempfile.TemporaryDirectory() as td:
        src = await _save_upload(file, Path(td))
        doc = _load_dxf(src)
        areas = _extract_from_doc(doc, patterns, src_types)

    factor = OUTPUT_UNITS[unit]
    total_m2 = sum(a.area_m2 for a in areas)
    return JSONResponse({
        "filename": file.filename,
        "unit": unit,
        "layers_requested": patterns,
        "source_types_requested": src_types,
        "count": len(areas),
        "total_area": round(total_m2 * factor, 6),
        "total_area_m2": round(total_m2, 6),
        "areas": [a.to_row(unit) for a in areas],
    })


@app.post("/export-excel")
async def export_excel(
    file: UploadFile = File(...),
    layers: str = Form("*"),
    source_types: str = Form("block_attr,hatch,lwpolyline_closed,polyline_closed"),
    unit: str = Form("m2"),
    sheet_name: str = Form("Suprafete"),
    format: str = Form("xlsx"),
) -> StreamingResponse:
    """Extract areas and return an XLSX or CSV with per-item rows and totals."""
    if unit not in OUTPUT_UNITS:
        raise HTTPException(400, f"unit must be one of {list(OUTPUT_UNITS)}")
    fmt = format.lower()
    if fmt not in ("xlsx", "csv"):
        raise HTTPException(400, "format must be 'xlsx' or 'csv'")
    patterns = _split_patterns(layers)
    src_types = _split_patterns(source_types)

    with tempfile.TemporaryDirectory() as td:
        src = await _save_upload(file, Path(td))
        doc = _load_dxf(src)
        areas = _extract_from_doc(doc, patterns, src_types)

    all_attr_keys: list[str] = []
    seen: set[str] = set()
    for a in areas:
        for k in a.attributes:
            if k not in seen:
                seen.add(k)
                all_attr_keys.append(k)

    header = ["#", "layer", "source_type", f"area_{unit}", "perimeter_m",
              "centroid_x", "centroid_y", *all_attr_keys]
    factor = OUTPUT_UNITS[unit]
    total_area = sum(a.area_m2 for a in areas) * factor
    fname_stem = re.sub(r"[^A-Za-z0-9._-]", "_", Path(file.filename or "cad").stem)

    if fmt == "csv":
        import csv
        text_buf = io.StringIO()
        w = csv.writer(text_buf)
        w.writerow(header)
        for i, a in enumerate(areas, 1):
            w.writerow([
                i, a.layer, a.source_type,
                round(a.area_m2 * factor, 6),
                round(a.perimeter_m, 3),
                round(a.centroid_x, 3),
                round(a.centroid_y, 3),
                *[a.attributes.get(k, "") for k in all_attr_keys],
            ])
        w.writerow([])
        w.writerow(["TOTAL", "", "", round(total_area, 6)])
        w.writerow([f"Source: {file.filename}"])
        w.writerow([f"Layers: {','.join(patterns)}"])
        buf = io.BytesIO(text_buf.getvalue().encode("utf-8-sig"))  # BOM for Excel-friendly UTF-8
        fname = f"{fname_stem}_areas_{unit}.csv"
        return StreamingResponse(
            buf, media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]
    ws.append(header)
    for i, a in enumerate(areas, 1):
        ws.append([
            i, a.layer, a.source_type,
            round(a.area_m2 * factor, 6),
            round(a.perimeter_m, 3),
            round(a.centroid_x, 3),
            round(a.centroid_y, 3),
            *[a.attributes.get(k, "") for k in all_attr_keys],
        ])

    total_row = len(areas) + 3
    ws.cell(row=total_row, column=1, value="TOTAL")
    ws.cell(row=total_row, column=4,
            value=f"=SUM(D2:D{len(areas) + 1})")
    ws.cell(row=total_row + 1, column=1, value=f"Source: {file.filename}")
    ws.cell(row=total_row + 2, column=1, value=f"Layers: {','.join(patterns)}")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = f"{fname_stem}_areas_{unit}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.post("/reconcile")
async def reconcile(
    dwg: UploadFile = File(...),
    xlsx: UploadFile = File(...),
    layers: str = Form("*"),
    source_types: str = Form("block_attr,hatch,lwpolyline_closed,polyline_closed"),
    unit: str = Form("m2"),
    xlsx_sheet: str = Form(""),
    xlsx_key_column: str = Form(...),
    xlsx_area_column: str = Form(...),
    dwg_key_attribute: str = Form(""),
    tolerance_pct: float = Form(0.5),
    tolerance_abs: float = Form(0.01),
) -> JSONResponse:
    """Compare DWG-extracted areas against an XLSX reference table.

    - The XLSX must contain a key column (parcel id) and an area column (in `unit`).
    - The DWG side matches on `dwg_key_attribute` if provided; otherwise
      matches on the row index order (fragile — prefer using block attributes).
    """
    if unit not in OUTPUT_UNITS:
        raise HTTPException(400, f"unit must be one of {list(OUTPUT_UNITS)}")

    with tempfile.TemporaryDirectory() as td:
        dwg_path = await _save_upload(dwg, Path(td))
        xlsx_path = await _save_upload(xlsx, Path(td))

        doc = _load_dxf(dwg_path)
        areas = _extract_from_doc(doc, _split_patterns(layers), _split_patterns(source_types))

        wb = load_workbook(xlsx_path, data_only=True, read_only=True)
        ws = wb[xlsx_sheet] if xlsx_sheet else wb.active
        rows_iter = ws.iter_rows(values_only=True)
        try:
            header = [str(c) if c is not None else "" for c in next(rows_iter)]
        except StopIteration:
            raise HTTPException(400, "XLSX is empty")

        if xlsx_key_column not in header:
            raise HTTPException(400,
                f"xlsx_key_column '{xlsx_key_column}' not found. Available: {header}")
        if xlsx_area_column not in header:
            raise HTTPException(400,
                f"xlsx_area_column '{xlsx_area_column}' not found. Available: {header}")

        key_idx = header.index(xlsx_key_column)
        area_idx = header.index(xlsx_area_column)

        xlsx_rows: dict[str, dict[str, Any]] = {}
        for row in rows_iter:
            if row is None or all(c is None for c in row):
                continue
            key = row[key_idx]
            if key is None:
                continue
            key_s = str(key).strip()
            try:
                area_val = float(str(row[area_idx]).replace(",", "."))
            except (TypeError, ValueError):
                area_val = float("nan")
            xlsx_rows[key_s] = {"area": area_val, "raw": {header[i]: row[i] for i in range(len(header)) if i < len(row)}}

    factor = OUTPUT_UNITS[unit]
    dwg_by_key: dict[str, ExtractedArea] = {}
    dwg_without_key: list[ExtractedArea] = []
    for a in areas:
        if dwg_key_attribute and dwg_key_attribute in a.attributes:
            dwg_by_key[str(a.attributes[dwg_key_attribute]).strip()] = a
        else:
            dwg_without_key.append(a)

    matched, area_diffs, missing_in_dwg, missing_in_xlsx = [], [], [], []
    for key, ref in xlsx_rows.items():
        if key in dwg_by_key:
            a = dwg_by_key[key]
            dwg_val = a.area_m2 * factor
            ref_val = ref["area"]
            diff = dwg_val - ref_val
            allowed = max(abs(ref_val) * (tolerance_pct / 100.0), tolerance_abs)
            ok = (not math.isnan(ref_val)) and abs(diff) <= allowed
            row = {
                "key": key,
                "xlsx_area": round(ref_val, 6),
                "dwg_area": round(dwg_val, 6),
                "diff": round(diff, 6),
                "diff_pct": round(diff / ref_val * 100.0, 4) if ref_val else None,
                "layer": a.layer,
                "source_type": a.source_type,
                "status": "ok" if ok else "diff",
            }
            (matched if ok else area_diffs).append(row)
        else:
            missing_in_dwg.append({"key": key, "xlsx_area": ref["area"]})

    for key in dwg_by_key:
        if key not in xlsx_rows:
            a = dwg_by_key[key]
            missing_in_xlsx.append({
                "key": key,
                "dwg_area": round(a.area_m2 * factor, 6),
                "layer": a.layer,
                "source_type": a.source_type,
            })

    total_xlsx = sum(r["area"] for r in xlsx_rows.values() if not math.isnan(r["area"]))
    total_dwg = sum(a.area_m2 for a in areas) * factor

    return JSONResponse({
        "unit": unit,
        "tolerance_pct": tolerance_pct,
        "tolerance_abs": tolerance_abs,
        "totals": {
            "xlsx": round(total_xlsx, 6),
            "dwg": round(total_dwg, 6),
            "diff": round(total_dwg - total_xlsx, 6),
        },
        "counts": {
            "xlsx_rows": len(xlsx_rows),
            "dwg_areas": len(areas),
            "matched_ok": len(matched),
            "matched_diff": len(area_diffs),
            "missing_in_dwg": len(missing_in_dwg),
            "missing_in_xlsx": len(missing_in_xlsx),
            "dwg_without_key": len(dwg_without_key),
        },
        "matched_ok": matched[:200],
        "matched_diff": area_diffs[:200],
        "missing_in_dwg": missing_in_dwg[:200],
        "missing_in_xlsx": missing_in_xlsx[:200],
        "notes": [
            "matched_ok / matched_diff / missing_* lists are capped at 200 rows for chat readability.",
            "If dwg_without_key > 0, some drawing entities lack the requested attribute — "
            "consider a different dwg_key_attribute or add TEXT-nearest-polyline matching.",
        ],
    })
