[English](README.md) | [Română](README.ro.md) | [Français](README.fr.md)

---

# Samples pour le service CAD

Fichiers de test pour le flux CAD (introspect / extract / export-excel / reconcile) — modélisés d'après un scénario réel d'expropriations routières en Roumanie.

## Contenu

| Fichier | Format | Description |
|---|---|---|
| [expropriere_sample.dxf](expropriere_sample.dxf) | DXF R2018, unités en mètres | Plan avec 11 blocs de parcelle (block attributes) + 2 polylignes fermées + 3 hachures + calques de bruit |
| [expropriere_sample.xlsx](expropriere_sample.xlsx) | XLSX, feuille `Parcele` | Tableau de référence avec 11 lignes : 10 parcelles existant dans le DXF + 1 fantôme |
| [generate.py](generate.py) | Python | Générateur reproductible — vous pouvez modifier les paramètres et régénérer |

## Ce qui est validé

Les samples sont conçus pour que le reconcile produise **exactement** le verdict suivant — un bon test de régression :


```
counts:  { xlsx_rows: 11, dwg_areas: 11,
           matched_ok: 9, matched_diff: 1,
           missing_in_dwg: 1, missing_in_xlsx: 1 }
totals:  { xlsx: 7776.25, dwg: 7714.94, diff: -61.31 }  m²
matched_diff:   [P-005: XLSX=300.00, DWG=315.00, Δ=+5.0%]
missing_in_dwg: [P-011]     # exists only in Excel
missing_in_xlsx:[P-EXTRA]   # exists only in drawing
```


Répartition prévue :

| Parcelle | XLSX (m²) | DXF (m²) | Attendu |
|---|---:|---:|---|
| P-001 … P-003 | 500 / 750 / 1200.50 | idem | `matched_ok` |
| P-004 | 480.00 | 480.24 | `matched_ok` (0.05% sous la tolerance de 0.5%) |
| P-005 | 300.00 | 315.00 | `matched_diff` (+5%) |
| P-006 … P-010 | valeurs fixes | idem | `matched_ok` |
| P-011 | 200.00 | — | `missing_in_dwg` |
| P-EXTRA | — | 123.45 | `missing_in_xlsx` |

## Structure du dessin DXF (après `introspect`)


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


## Utilisation

### 1) Test rapide direct sur l'API (curl)


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


### 2) Test end-to-end depuis Open WebUI

1. Ouvrez http://localhost:8080
2. Téléchargez localement les deux fichiers depuis `cad-service/samples/`
3. Dans le chat, **joignez les deux fichiers** (📎) et écrivez :
   > « Vérifie les superficies des parcelles du dessin par rapport à l'Excel. »
4. Le modèle appelle `cad_introspect` → vous demande quel calque/colonne utiliser. Répondez :
   > « Calque PARCELE_EXPROPRIERE, clé NR_PARCELA dans le DWG et Nr_parcela / Suprafata_masurata_mp dans l'Excel. »
5. Le modèle appelle `cad_reconcile` avec vos paramètres et génère le rapport.

Résultat attendu dans le chat :


```
Verificat 11 parcele:
- ✅ 9 OK
- ⚠️ 1 diferă peste toleranță:
    P-005: XLSX=300.00 m², DWG=315.00 m² (Δ +5.0%)
- ❌ 1 lipsește din DWG: P-011
- ❌ 1 doar în DWG (fără corespondent Excel): P-EXTRA
Total: XLSX 7776.25 m² vs DWG 7714.94 m² (Δ -61.31 m²)
```


### 3) Régénération / modification


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


## Remarques

- Les fichiers ne sont **pas** inclus dans l'image Docker `cad-service:local` — le `Dockerfile` copie uniquement `app.py` et `requirements.txt`.
- Le fichier DXF est généré avec `$INSUNITS=6` (mètres) — si vous souhaitez simuler un dessin en mm, modifiez la valeur à `4` dans `generate.py` et les fichiers produits auront des coordonnées mises à l'échelle ×1000.
- Vous pouvez utiliser le même dessin pour l'ensemble des 4 endpoints ; le fichier XLSX est requis uniquement pour `reconcile`.