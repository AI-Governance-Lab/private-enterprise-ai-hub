# Samples pentru CAD service

Fișiere de test pentru fluxul CAD (introspect / extract / export-excel / reconcile) — modelate după un scenariu real de exproprieri drumuri România.

## Ce conține

| Fișier | Format | Ce reprezintă |
|---|---|---|
| [expropriere_sample.dxf](expropriere_sample.dxf) | DXF R2018, unități metri | Planșă cu 11 blocuri de parcelă (block attributes) + 2 polilinii închise + 3 hatch-uri + layere de zgomot |
| [expropriere_sample.xlsx](expropriere_sample.xlsx) | XLSX, sheet `Parcele` | Tabel de referință cu 11 rânduri: 10 parcele care există în DXF + 1 fantomă |
| [generate.py](generate.py) | Python | Generator reproductibil — poți schimba parametrii și regenera |

## Ce validează

Sample-urile sunt proiectate ca reconcile-ul să scoată **exact** următorul verdict — bun test de regresie:

```
counts:  { xlsx_rows: 11, dwg_areas: 11,
           matched_ok: 9, matched_diff: 1,
           missing_in_dwg: 1, missing_in_xlsx: 1 }
totals:  { xlsx: 7776.25, dwg: 7714.94, diff: -61.31 }  m²
matched_diff:   [P-005: XLSX=300.00, DWG=315.00, Δ=+5.0%]
missing_in_dwg: [P-011]     # exists only in Excel
missing_in_xlsx:[P-EXTRA]   # exists only in drawing
```

Distribuția intenționată:

| Parcelă | XLSX (m²) | DXF (m²) | Așteptat |
|---|---:|---:|---|
| P-001 … P-003 | 500 / 750 / 1200.50 | idem | `matched_ok` |
| P-004 | 480.00 | 480.24 | `matched_ok` (0.05% sub tolerance 0.5%) |
| P-005 | 300.00 | 315.00 | `matched_diff` (+5%) |
| P-006 … P-010 | valori fixe | idem | `matched_ok` |
| P-011 | 200.00 | — | `missing_in_dwg` |
| P-EXTRA | — | 123.45 | `missing_in_xlsx` |

## Structura desenului DXF (după `introspect`)

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

## Cum le folosești

### 1) Test rapid direct pe API (curl)

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

### 2) Test end-to-end din Open WebUI

1. Deschide http://localhost:8080
2. Descarcă local ambele fișiere din `cad-service/samples/`
3. În chat, **atașează ambele** (📎) și scrie:
   > „Verifică ariile parcelelor din desen față de Excel."
4. Modelul apelează `cad_introspect` → te întreabă care layer/coloană. Răspunde:
   > „Layer PARCELE_EXPROPRIERE, cheie NR_PARCELA în DWG și Nr_parcela / Suprafata_masurata_mp în Excel."
5. Modelul apelează `cad_reconcile` cu parametrii tăi și scoate raportul.

Rezultatul așteptat în chat:

```
Verificat 11 parcele:
- ✅ 9 OK
- ⚠️ 1 diferă peste toleranță:
    P-005: XLSX=300.00 m², DWG=315.00 m² (Δ +5.0%)
- ❌ 1 lipsește din DWG: P-011
- ❌ 1 doar în DWG (fără corespondent Excel): P-EXTRA
Total: XLSX 7776.25 m² vs DWG 7714.94 m² (Δ -61.31 m²)
```

### 3) Regenerare / modificare

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

## Note

- Fișierele **nu** sunt incluse în imaginea Docker `cad-service:local` — `Dockerfile` copiază doar `app.py` și `requirements.txt`.
- DXF-ul e generat cu `$INSUNITS=6` (metri) — dacă vrei să simulezi un desen în mm, schimbă în `generate.py` la `4` și fișierele produse vor fi cu coordonate scalate ×1000.
- Poți folosi același desen pentru toate cele 4 endpoint-uri; XLSX-ul e necesar doar pentru `reconcile`.
