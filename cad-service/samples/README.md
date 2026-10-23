[English](README.md) | [Română](README.ro.md) | [Français](README.fr.md)

---

# Samples for CAD service

Test files for the CAD workflow (introspect / extract / export-excel / reconcile) — modeled after a real-world road expropriation scenario in Romania.

## What it contains

| File | Format | What it represents |
|---|---|---|
| [expropriere_sample.dxf](expropriere_sample.dxf) | DXF R2018, meter units | Drawing sheet with 11 parcel blocks (block attributes) + 2 closed polylines + 3 hatches + noise layers |
| [expropriere_sample.xlsx](expropriere_sample.xlsx) | XLSX, sheet `Parcele` | Reference table with 11 rows: 10 parcels that exist in the DXF + 1 ghost parcel |
| [generate.py](generate.py) | Python | Reproducible generator — you can change parameters and regenerate |

## What it validates

The samples are designed so that the reconcile process outputs **exactly** the following verdict — a solid regression test:


```
counts:  { xlsx_rows: 11, dwg_areas: 11,
           matched_ok: 9, matched_diff: 1,
           missing_in_dwg: 1, missing_in_xlsx: 1 }
totals:  { xlsx: 7776.25, dwg: 7714.94, diff: -61.31 }  m²
matched_diff:   [P-005: XLSX=300.00, DWG=315.00, Δ=+5.0%]
missing_in_dwg: [P-011]     # exists only in Excel
missing_in_xlsx:[P-EXTRA]   # exists only in drawing
```


Intended distribution:

| Parcel | XLSX (m²) | DXF (m²) | Expected |
|---|---:|---:|---|
| P-001 … P-003 | 500 / 750 / 1200.50 | same | `matched_ok` |
| P-004 | 480.00 | 480.24 | `matched_ok` (0.05% below 0.5% tolerance) |
| P-005 | 300.00 | 315.00 | `matched_diff` (+5%) |
| P-006 … P-010 | fixed values | same | `matched_ok` |
| P-011 | 200.00 | — | `missing_in_dwg` |
| P-EXTRA | — | 123.45 | `missing_in_xlsx` |

## DXF drawing structure (after `introspect`)


```
7 layers, units: m
  AX_DRUM                 total= 1  line=1                 # decorative noise
  CONTUR                  total= 1  lwpolyline_closed=1    # decorative noise
  PARCELE_EXPROPRIERE     total=11  insert=11              # ← blocks with attributes (authoritative)
  PARCELE_POLILINII       total= 2  lwpolyline_closed=2    # pattern fallback
  S_EXPROPRIERE_DEFINITIV total= 2  hatch=2                # 400 m² + 450 m²
  S_EXPROPRIERE_TEMPORAR  total= 1  hatch=1                # 500 m²
  TEXT_INFO               total= 1  text=1                 # drawing title

block attribute keys:
  NR_PARCELA (11), SUPRAFATA_MP (11), PROPRIETAR (11)
```


## How to use them

### 1) Quick test directly via the API (curl)


```bash
# introspect
docker cp cad-service/samples/expropriere_sample.dxf cad-service:/tmp/
docker exec cad-service curl -sS -X POST \
    -F "file=@/tmp/expropriere_sample.dxf" \
    http://127.0.0.1:8090/introspect | python3 -m json.tool

# extract (authoritative parcels only)
docker exec cad-service curl -sS -X POST \
    -F "file=@/tmp/expropriere_sample.dxf" \
    -F "layers=PARCELE_EXPROPRIERE" \
    -F "unit=m2" \
    http://127.0.0.1:8090/extract | python3 -m json.tool

# export-excel — saved to host
docker exec cad-service curl -sS -X POST \
    -F "file=@/tmp/expropriere_sample.dxf" \
    -F "layers=PARCELE_EXPROPRIERE" \
    -o /tmp/out.xlsx http://127.0.0.1:8090/export-excel
docker cp cad-service:/tmp/out.xlsx ./areas_extracted.xlsx

# reconcile
docker cp cad-service/samples/expropriere_sample.xlsx cad-service:/tmp/
docker exec cad-service curl -sS -X POST \
    -F "dwg=@/tmp/expropriere_sample.dxf" \
    -F "xlsx=@/tmp/expropriere_sample.xlsx" \
    -F "layers=PARCELE_EXPROPRIERE" \
    -F "xlsx_key_column=Nr_parcela" \
    -F "xlsx_area_column=Suprafata_masurata_mp" \
    -F "dwg_key_attribute=NR_PARCELA" \
    -F "unit=m2" -F "tolerance_pct=0.5" \
    http://127.0.0.1:8090/reconcile | python3 -m json.tool
```


### 2) End-to-end test from Open WebUI

1. Open http://localhost:8080
2. Download both files locally from `cad-service/samples/`
3. In the chat, **attach both** (📎) and write:
   > "Check the parcel areas in the drawing against Excel."
4. The model calls `cad_introspect` → asks you which layer/column. Reply:
   > "Layer PARCELE_EXPROPRIERE, key NR_PARCELA in DWG and Nr_parcela / Suprafata_masurata_mp in Excel."
5. The model calls `cad_reconcile` with your parameters and outputs the report.

Expected result in chat:


```
Verificat 11 parcele:
- ✅ 9 OK
- ⚠️ 1 diferă peste toleranță:
    P-005: XLSX=300.00 m², DWG=315.00 m² (Δ +5.0%)
- ❌ 1 lipsește din DWG: P-011
- ❌ 1 doar în DWG (fără corespondent Excel): P-EXTRA
Total: XLSX 7776.25 m² vs DWG 7714.94 m² (Δ -61.31 m²)
```


### 3) Regeneration / modification


```bash
# Edit generate.py (change parcels, tolerances, etc.)
$EDITOR cad-service/samples/generate.py

# Run inside container (has ezdxf + openpyxl)
docker cp cad-service/samples/generate.py cad-service:/tmp/generate.py
docker exec cad-service python3 /tmp/generate.py

# Copy back to host
docker cp cad-service:/tmp/expropriere_sample.dxf cad-service/samples/
docker cp cad-service:/tmp/expropriere_sample.xlsx cad-service/samples/
```


## Notes

- The files are **not** included in the `cad-service:local` Docker image — the `Dockerfile` only copies `app.py` and `requirements.txt`.
- The DXF is generated with `$INSUNITS=6` (meters) — if you want to simulate a drawing in mm, change it to `4` in `generate.py`, and the generated files will have coordinates scaled ×1000.
- You can use the same drawing for all 4 endpoints; the XLSX is only required for `reconcile`.