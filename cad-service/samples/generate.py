"""Reproducible generator for a realistic Romanian road-expropriation test dataset.

Produces two files in the current directory:

- `expropriere_sample.dxf` — a DXF R2018 in meters with:
    * layer PARCELE_EXPROPRIERE — 11 blocks with attributes NR_PARCELA,
      SUPRAFATA_MP, PROPRIETAR (10 that also exist in the XLSX + 1 extra
      to test `missing_in_xlsx`)
    * layer PARCELE_POLILINII — 2 closed LWPOLYLINEs (fallback pattern
      when no block attributes are used)
    * layer S_EXPROPRIERE_DEFINITIV — 2 HATCHes
    * layer S_EXPROPRIERE_TEMPORAR — 1 HATCH
    * layers AX_DRUM, CONTUR, TEXT_INFO — decorative noise so introspect
      still has to sift through them

- `expropriere_sample.xlsx` — 12 rows on sheet "Parcele":
    * columns: Nr_parcela | Denumire_UAT | Categorie | Proprietar | Suprafata_masurata_mp
    * 9 rows match the DXF blocks exactly
    * 1 row (P-004) has +0.05% diff vs. DXF — within default 0.5% tolerance (OK)
    * 1 row (P-005) has +5% diff vs. DXF — flagged as `matched_diff`
    * 1 row (P-011) does NOT exist in DXF — flagged as `missing_in_dwg`
    * The DXF has 1 extra block (P-EXTRA) that is NOT in XLSX — flagged as
      `missing_in_xlsx`

Run inside the cad-service container (which has ezdxf + openpyxl):
    docker exec cad-service python3 /tmp/generate.py
Then copy files out:
    docker cp cad-service:/tmp/expropriere_sample.dxf ./samples/
    docker cp cad-service:/tmp/expropriere_sample.xlsx ./samples/
"""
from __future__ import annotations

import math
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment
from openpyxl import Workbook

OUT_DIR = Path(__file__).resolve().parent
DXF_PATH = OUT_DIR / "expropriere_sample.dxf"
XLSX_PATH = OUT_DIR / "expropriere_sample.xlsx"

# Parcels: (nr, uat, categorie, proprietar, xlsx_area, dxf_attr_area)
# When xlsx_area != dxf_attr_area we get a diff row in reconcile.
PARCELS = [
    ("P-001", "Bragadiru",   "Arabil",   "Ionescu Ion",         500.00,  500.00),  # OK
    ("P-002", "Bragadiru",   "Arabil",   "Popescu Maria",       750.00,  750.00),  # OK
    ("P-003", "Bragadiru",   "Livada",   "Popa Constantin",    1200.50, 1200.50),  # OK
    ("P-004", "Cornetu",     "Arabil",   "Georgescu Vasile",    480.00,  480.24),  # <0.5% -> OK
    ("P-005", "Cornetu",     "Fanete",   "Dumitrescu Ana",      300.00,  315.00),  # +5% -> DIFF
    ("P-006", "Cornetu",     "Arabil",   "Radu Petru",          950.00,  950.00),  # OK
    ("P-007", "Ciorogarla",  "Padure",   "Manole Grigore",     1500.00, 1500.00),  # OK
    ("P-008", "Ciorogarla",  "Arabil",   "Iordache Elena",      620.75,  620.75),  # OK
    ("P-009", "Ciorogarla",  "Curti",    "Neagu Alexandru",     830.00,  830.00),  # OK
    ("P-010", "Domnesti",    "Arabil",   "Stan Nicoleta",       445.00,  445.00),  # OK
    # In XLSX only (missing_in_dwg):
    ("P-011", "Domnesti",    "Livada",   "Barbu Florin",        200.00,  None),
    # In DWG only (missing_in_xlsx):
    ("P-EXTRA", None,        None,       None,                  None,    123.45),
]


def _make_marker_block(doc):
    """Small square used as visible geometry inside each parcel block."""
    blk = doc.blocks.new(name="PARCELA_MARKER")
    blk.add_lwpolyline([(-1, -1), (1, -1), (1, 1), (-1, 1)], close=True)
    for tag, y in (("NR_PARCELA", 3), ("SUPRAFATA_MP", 5), ("PROPRIETAR", 7)):
        blk.add_attdef(tag, insert=(0, y), dxfattribs={"height": 1.5, "layer": "TEXT_INFO"})


def _add_hatch(msp, layer: str, poly_pts):
    hatch = msp.add_hatch(color=1, dxfattribs={"layer": layer})
    hatch.paths.add_polyline_path(poly_pts, is_closed=True)


def build_dxf() -> None:
    doc = ezdxf.new(dxfversion="R2018", setup=True)
    doc.header["$INSUNITS"] = 6  # meters
    msp = doc.modelspace()

    for name in ("PARCELE_EXPROPRIERE", "PARCELE_POLILINII",
                 "S_EXPROPRIERE_DEFINITIV", "S_EXPROPRIERE_TEMPORAR",
                 "AX_DRUM", "CONTUR", "TEXT_INFO"):
        doc.layers.add(name)

    _make_marker_block(doc)

    # Blocks with attributes — the authoritative parcel source.
    x_cursor = 0.0
    for nr, uat, cat, prop, _xlsx_area, dxf_area in PARCELS:
        if dxf_area is None:
            continue
        insert = msp.add_blockref(
            "PARCELA_MARKER", (x_cursor, 0),
            dxfattribs={"layer": "PARCELE_EXPROPRIERE"},
        )
        insert.add_auto_attribs({
            "NR_PARCELA": nr,
            "SUPRAFATA_MP": f"{dxf_area:.2f}",
            "PROPRIETAR": prop or "-",
        })
        x_cursor += 15.0

    # Two closed polylines (fallback pattern) on a separate layer.
    # Rectangle 40x25 = 1000 m2
    msp.add_lwpolyline(
        [(200, 0), (240, 0), (240, 25), (200, 25)],
        close=True, dxfattribs={"layer": "PARCELE_POLILINII"},
    )
    # Trapezoid: bases 30 and 50 at height 40, area = (30+50)/2 * 40 = 1600 m2
    msp.add_lwpolyline(
        [(260, 0), (310, 0), (300, 40), (270, 40)],
        close=True, dxfattribs={"layer": "PARCELE_POLILINII"},
    )

    # Hatches — definitive and temporary expropriation areas
    # HATCH 1: 20x20 square = 400 m2 (definitive)
    _add_hatch(msp, "S_EXPROPRIERE_DEFINITIV",
               [(400, 0), (420, 0), (420, 20), (400, 20)])
    # HATCH 2: 15x30 rectangle = 450 m2 (definitive)
    _add_hatch(msp, "S_EXPROPRIERE_DEFINITIV",
               [(440, 0), (455, 0), (455, 30), (440, 30)])
    # HATCH 3: 10x50 rectangle = 500 m2 (temporary)
    _add_hatch(msp, "S_EXPROPRIERE_TEMPORAR",
               [(500, 0), (510, 0), (510, 50), (500, 50)])

    # Decorative noise — helps prove introspect must actually filter layers.
    msp.add_line((-50, -50), (600, -50), dxfattribs={"layer": "AX_DRUM"})
    msp.add_lwpolyline(
        [(-60, -60), (610, -60), (610, 60), (-60, 60)],
        close=True, dxfattribs={"layer": "CONTUR"},
    )
    msp.add_text(
        "SECTOR EXPROPRIERE km 5+000 - km 5+500", height=3.0,
        dxfattribs={"layer": "TEXT_INFO"},
    ).set_placement((0, -80), align=TextEntityAlignment.LEFT)

    doc.saveas(str(DXF_PATH))
    print(f"DXF written: {DXF_PATH}")


def build_xlsx() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Parcele"
    ws.append(["Nr_parcela", "Denumire_UAT", "Categorie",
               "Proprietar", "Suprafata_masurata_mp"])
    for nr, uat, cat, prop, xlsx_area, _ in PARCELS:
        if xlsx_area is None:
            continue
        ws.append([nr, uat, cat, prop, xlsx_area])
    wb.save(XLSX_PATH)
    print(f"XLSX written: {XLSX_PATH}")


if __name__ == "__main__":
    build_dxf()
    build_xlsx()
    print("Done.")
