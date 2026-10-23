# CAD Service — DWG/DXF ⇄ XLSX pentru exproprieri drumuri 🛣️📐

Modul opțional adăugat peste stack-ul principal ([README.md](README.md)) care extrage suprafețele (parcele) dintr-un desen AutoCAD, produce XLSX-uri și verifică coerența față de tabelul cadastral de referință.

Se instalează și se pornește prin același `run.sh`. Dacă build-ul sau pornirea eșuează, **restul stack-ului continuă să funcționeze** — vezi [Fail-safe design](#fail-safe-design) mai jos.

---

## 🎯 Ce face

Trei fluxuri de bază, comandate din chat prin Gemini Pro/Flash:

1. **Descoperă** ce e în DWG (`cad_introspect`) — modelul primește lista de layere și atribute de bloc, apoi te întreabă „care sunt layerele parcelelor?" și „ce coloană din Excel e cheia?". Nimic hardcodat.
2. **Extrage** suprafețele (`cad_extract`, `cad_to_excel`) — arii calculate în m² / ha / km², cu totaluri. Poți primi rezultatul ca JSON în chat sau ca fișier XLSX descărcabil.
3. **Verifică** (`cad_reconcile`) — compară arii DWG cu un XLSX de referință; scoate raport cu diferențe peste toleranță, parcele lipsă, parcele fantomă.

Formate acceptate: **`.dwg`** (AutoCAD 2018+ testat via libredwg; upgrade la ODA File Converter dacă ai fișiere problematice — vezi mai jos) și **`.dxf`** (ASCII sau binary).

---

## 🏗️ Arhitectură

```
Browser ──► Open WebUI ──► LLM (Gemini via LiteLLM) ──► tool cad_*
                                                            │
                                                            ▼ HTTP intern
                                                    ┌─────────────────┐
                                                    │  cad-service    │
                                                    │  FastAPI :8090  │
                                                    │  ezdxf +        │
                                                    │  libredwg +     │
                                                    │  openpyxl       │
                                                    └─────────────────┘
```

- Container `cad-service` pe rețeaua `private-ai-net` (nu se expune afară — nu are port publicat).
- Comunică doar prin DNS intern: `http://cad-service:8090`.
- Stateless: nu are volum persistent, nu ține date.
- Tool-urile Python rulează în procesul Open WebUI și fac HTTP la `cad-service`.

---

## 📁 Fișiere adăugate

```
cad-service/
├── Dockerfile             # Python 3.11 + libredwg-tools + ezdxf + openpyxl
├── requirements.txt
├── app.py                 # FastAPI: /health /introspect /extract /export-excel /reconcile
└── samples/               # Fișiere de test (DXF + XLSX) — vezi samples/README.md
    ├── README.md
    ├── generate.py
    ├── expropriere_sample.dxf
    └── expropriere_sample.xlsx

openwebui-tools/
└── cad_tool.py            # Se importă manual în Open WebUI: Workspace → Tools → Import
```

`run.sh` a fost extins cu o secțiune opțională (activată default) care construiește imaginea local și pornește containerul.

---

## 🚀 Deploy

### First-time (containerul e adăugat la un stack existent)

```bash
cd /opt/private-enterprise-ai-hub
./run.sh
```

Script-ul:
1. face `docker build -t cad-service:local cad-service/`
2. pornește containerul pe rețeaua `private-ai-net`
3. la sfârșit afișează `CAD service status: up | build_failed | start_failed | skipped`

### Dezactivare

Dacă vrei să sari peste el temporar:

```bash
CAD_SERVICE_ENABLED=0 ./run.sh
```

### Rebuild după modificări în cod

```bash
docker build -t cad-service:local /opt/private-enterprise-ai-hub/cad-service/
docker rm -f cad-service
./run.sh
```

### Import tool în Open WebUI (o singură dată)

1. Deschide `http://localhost:8080`
2. Workspace → **Tools** → **Import from file**
3. Uploadeaz-o pe `openwebui-tools/cad_tool.py`
4. Activează tool-ul pentru modelele **Gemini Pro** și/sau **AI Assistant Flash**:
   Admin → Models → *Model* → Tools → bifează `CAD Tools`

---

## 📤 Cum urcă userul fișierele

Modelul **nu primește URL-uri sau id-uri de fișier** — Open WebUI injectează automat kwarg-ul special `__files__` în tool-uri când există fișiere atașate mesajului. Tool-urile CAD selectează singure fișierele după extensie (`.dwg`/`.dxf` pentru desen, `.xlsx` pentru referință).

**Pași user:**

1. În chat, atașează fișierele la mesaj cu 📎 (Attach):
   - Pentru extract/introspect/to-excel: un singur `.dwg` sau `.dxf`.
   - Pentru reconcile: **ambele** — `.dwg` (sau `.dxf`) și `.xlsx` — pe **același** mesaj.
2. În mesaj scrie ce vrei (ex: „scanează layerele" sau „verifică ariile cu Excel-ul").
3. Modelul apelează tool-ul potrivit fără să-i dai id-uri sau URL-uri.

**Fișierele acceptate:**
- Open WebUI acceptă orice extensie by default (`RAG_ALLOWED_FILE_EXTENSIONS=[]`, fără limită de mărime).
- Fișierele sunt salvate pe RAID la `/mnt/raid1/podman-volumes/open-webui-data/uploads/{uuid}_{filename}` — persistente între restart-uri.

**Recomandare pentru fișiere CAD mari:**
- La upload, click pe fișier → toggle **„Bypass Embedding and Retrieval"** → ON. Asta oprește Open WebUI să încerce indexare RAG pe binaruri CAD (n-are sens, ar pollua vector DB-ul cu bytes brute). Tool-ul CAD are acces direct la fișierul pe disk indiferent de această setare.

**Când user-ul urcă unul singur din 2 fișiere așteptate:**

Modelul primește un mesaj de eroare structurat, nu o excepție:
```json
{
  "error": "missing_files",
  "action": "reconcile",
  "need": ["an .xlsx reference table"],
  "attached_now": ["km_12+300.dwg"],
  "hint": "Ask the user to attach both files to the same chat message."
}
```
Modelul îi cere userului fișierul lipsă în limba conversației.

---

## 🧪 Verificare post-deploy

```bash
# 1. Is container running?
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep cad-service

# 2. Health check OK? (from internal network)
docker exec open-webui curl -s http://cad-service:8090/health | python3 -m json.tool

# Expected response:
# {
#   "status": "ok",
#   "converter": "dwg2dxf",
#   "converter_ok": true,
#   "converter_version": "libredwg 0.12.5 ...",
#   "ezdxf_version": "1.3.5",
#   "max_upload_mb": 500
# }
```

Dacă `status` e `degraded`, converter-ul DWG nu răspunde — funcționează doar DXF până rezolvi (vezi troubleshooting).

---

## 🔌 API — endpoint-uri

Toate cu payload `multipart/form-data`. Port intern **8090** (nu publicat afară).

### `GET /health`

Health-check + versiuni.

### `POST /introspect`

**Form:** `file: UploadFile`

**Răspuns (extras):**
```json
{
  "filename": "planse_km_12+300_12+800.dwg",
  "dxf_version": "AC1032",
  "insunits_code": 6, "meters_per_unit": 1.0, "unit_label": "m",
  "layer_count": 47,
  "layers": [
    {"name": "S_EXPROPRIERE_DEFINITIV", "total": 132, "hatch": 128, "lwpolyline_closed": 4, "insert": 0, ...},
    {"name": "PARCELA_CADASTRAL", "total": 128, "insert": 128, ...}
  ],
  "block_attribute_keys": [
    {"tag": "NR_PARCELA", "count": 128},
    {"tag": "SUPRAFATA_MP", "count": 128},
    {"tag": "PROPRIETAR", "count": 128}
  ]
}
```

### `POST /extract`

**Form:**
- `file: UploadFile`
- `layers` = `"*"` (glob comma-separated, ex: `"S_EXPROPRIERE_*,PARCELA_*"`)
- `source_types` = `"block_attr,hatch,lwpolyline_closed,polyline_closed"` — care tipuri de entități
- `unit` = `"m2" | "ha" | "km2"`

Răspuns: JSON cu `areas[]`, `total_area`, `count`.

### `POST /export-excel`

Aceeași input ca `/extract` + `sheet_name`. Răspuns: fișier **XLSX** cu `Content-Disposition: attachment`.

### `POST /reconcile`

**Form:**
- `dwg: UploadFile`
- `xlsx: UploadFile`
- `xlsx_key_column` — numele coloanei-cheie în XLSX (ex: `Nr_parcela`)
- `xlsx_area_column` — coloana cu aria (ex: `Suprafata_masurata_mp`)
- `dwg_key_attribute` — tag-ul de bloc care ține id-ul parcelei (ex: `NR_PARCELA`)
- `layers`, `source_types`, `unit` (ca la extract)
- `xlsx_sheet` (opțional; blank = active sheet)
- `tolerance_pct` (default `0.5`)
- `tolerance_abs` (default `0.01`)

Răspuns: totaluri, contorizări, `matched_ok`, `matched_diff` (peste toleranță), `missing_in_dwg`, `missing_in_xlsx`. Listele sunt capped la 200 rânduri.

---

## 💬 Cum arată un flux tipic în chat

```
User: [📎 atașează km_12+300.dwg]  [📎 atașează expropriere_km_12+300.xlsx]
      Verifică ariile.

Model: [apelează cad_introspect() — nu-i dă niciun argument;
        tool-ul găsește .dwg-ul singur din __files__]

       "Desenul are 47 de layere. Am găsit 4 care par să conțină suprafețe:
        - S_EXPROPRIERE_DEFINITIV (132 hatch-uri)
        - S_EXPROPRIERE_TEMPORAR  (56 hatch-uri)
        - PARCELA_CADASTRAL       (128 blocuri cu atribute NR_PARCELA, SUPRAFATA_MP)
        - CONSTRUCTII_EXISTENTE   (12 hatch-uri)

        Care sunt layerele parcelelor de verificat? Bănuiesc PARCELA_CADASTRAL — confirmi?
        Îmi trebuie și numele coloanelor din Excel: care e cheia (Nr_parcela?)
        și care e aria (Suprafata_masurata_mp?)."

User: da, PARCELA_CADASTRAL. In excel: Nr_parcela + Suprafata_masurata_mp.
      toleranta 0.1%.

Model: [apelează cad_reconcile(
          layers='PARCELA_CADASTRAL',
          dwg_key_attribute='NR_PARCELA',
          xlsx_key_column='Nr_parcela',
          xlsx_area_column='Suprafata_masurata_mp',
          tolerance_pct=0.1
        ) — tool-ul găsește ambele fișiere singur]

        "Verificat 128 parcele:
         - ✅ 121 OK (sub 0.1% diferență)
         - ⚠️ 5 diferă peste toleranță:
             #A7-023: XLSX=1240.50 m², DWG=1247.83 m² (Δ +0.59%)
             #A7-041: XLSX=890.10 m²,  DWG=901.44 m²  (Δ +1.27%)
             ...
         - ❌ 2 lipsesc din DWG: A7-055, A7-091
         Total: XLSX 187,432 m² vs DWG 187,890 m² (Δ +458 m²)"
```

---

## 🛡️ Fail-safe design

**Ce se întâmplă dacă `cad-service` e down:**

1. `run.sh` afișează `CAD service status: build_failed` sau `start_failed`, dar **restul stack-ului pornește normal**.
2. Când modelul cheamă un tool CAD, primește un JSON de eroare clar:
   ```json
   {
     "error": "cad_service_unavailable",
     "action": "introspect",
     "detail": "ConnectError: [Errno -2] Name or service not known",
     "hint": "Restul chat-ului funcționează. Verifică: docker ps | grep cad-service"
   }
   ```
3. Modelul va spune userului „serviciul CAD nu răspunde acum" și continuă normal cu restul întrebărilor (chat, RAG, web search, Vertex AI).

**Cum verifici starea:**
```bash
docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep cad
docker logs cad-service --tail 50
```

---

## 🚨 Troubleshooting

### `CAD service status: build_failed`
- **Cauza:** apt/pip a picat sau build context lipsit
- **Verifică:** `cat /tmp/cad-build.log | tail -50`
- **Fix comun:** rulează `docker system prune -f` să eliberezi spațiu, apoi re-run `./run.sh`

### `CAD service status: start_failed`
- **Cauza:** portul intern e ocupat sau imaginea nu s-a construit
- **Verifică:** `cat /tmp/cad-run.log`

### `converter_ok: false` în /health
- **Cauza:** `dwg2dxf` (libredwg) lipsește din imagine
- **Fix:** rebuild imagine — `docker build -t cad-service:local cad-service/`

### `500 DWG->DXF conversion failed`
- **Cauza:** fișier DWG nou (AC1032 / AC1035) pe care libredwg nu îl citește
- **Fix rapid:** salvează din AutoCAD ca DXF ASCII sau ca DWG 2013 și reîncearcă
- **Fix definitiv:** upgrade la ODA File Converter (mai jos)

### Ariile sunt aiurea (prea mari sau prea mici)
- **Cauza:** unitățile modelului DWG nu sunt cele așteptate. Cadastrul RO e uzual în metri, dar unii lucrează în mm.
- **Verifică:** răspunsul `/introspect` conține `insunits_code` și `unit_label`. Dacă e `mm` (`insunits_code=4`), scalarea se face automat.
- **Dacă e `unspecified` (code=0)**, serviciul presupune metri. Corectează salvând DWG-ul cu `INSUNITS` setat.

### `413 File too large`
- **Cauza:** fișier > 500 MB
- **Fix:** override la deploy: în `run.sh` schimbă `-e MAX_UPLOAD_MB=500` la valoarea dorită și redeploy

### Tool-ul CAD nu apare în chat
- Verifică că l-ai importat din UI (Workspace → Tools) — nu se face automat
- Verifică că e activat pentru modelul folosit (Admin → Models → *Model* → Tools)

### Tool-ul răspunde cu `no_matching_file_attached`
- **Cauza:** ai scris comanda dar n-ai atașat fișierul (sau ai atașat cu extensia greșită).
- **Fix:** click pe 📎 din bara de mesaje și adaugă `.dwg` / `.dxf` (sau `.xlsx` pentru reconcile). Retrimite mesajul.

### Tool-ul răspunde cu `file_not_on_disk`
- **Cauza:** WebUI a înregistrat file_id-ul dar path-ul așteptat (`/app/backend/data/uploads/{id}_{name}`) nu există.
- **Fix:** verifică volumul din container: `docker exec open-webui ls /app/backend/data/uploads/ | grep <id>`. Dacă lipsește, re-uploadeaz-o (probabil upload-ul a picat parțial).

### RAG-ul pare „murdărit" după upload de fișier CAD
- **Cauza:** Open WebUI trece implicit orice upload prin Tika pentru RAG. DXF ASCII poate produce chunk-uri de coordonate brute.
- **Fix:** la upload, click pe fișierul CAD → activează **„Bypass Embedding and Retrieval"**. Tool-ul CAD merge oricum — nu depinde de RAG.

### `cad-service` inaccesibil sau eroare de rezoluție din Open WebUI (`Temporary failure in name resolution`)
- **Cauza:** Reîncărcarea firewall-ului gazdei (`firewall-cmd --reload`) a resetat regulile dinamice Podman (`netavark`), blocând interogările DNS pe `10.89.0.1:53`.
- **Fix:** Rețeaua Podman a fost adăugată în zona `trusted` a firewall-ului, iar serviciul `netavark-firewalld-reload.service` a fost activat permanent. Vezi secțiunea dedicată de troubleshooting din [vscode.md](vscode.md).

---

## ⬆️ Upgrade la ODA File Converter (recomandat pentru DWG 2018+)

libredwg funcționează pe majoritatea DWG-urilor, dar are lag față de formatele foarte noi. ODA File Converter (Open Design Alliance, free, closed-source) e standardul industriei.

**Pași:**

1. Descarcă `.deb` pentru Linux x86_64 de la:
   <https://www.opendesign.com/guestfiles/oda_file_converter>
   (necesită înregistrare gratuită)
2. Pune fișierul în `cad-service/` (ex: `ODAFileConverter_QT6_lnxX64_8.3dll_25.3.deb`)
3. Decomentează blocul din `cad-service/Dockerfile`:
   ```dockerfile
   COPY ODAFileConverter_*.deb /tmp/oda.deb
   RUN apt-get update && apt-get install -y --no-install-recommends /tmp/oda.deb \
       xvfb libglu1-mesa && rm -rf /var/lib/apt/lists/* /tmp/oda.deb
   ```
4. Modifică `app.py` → funcția `_convert_dwg_to_dxf` să apeleze `ODAFileConverter` în loc de `dwg2dxf`
5. Rebuild + redeploy: `docker build -t cad-service:local cad-service/ && docker rm -f cad-service && ./run.sh`

---

## 🔒 Securitate & izolare

- Portul 8090 e **doar intern** (rețeaua Docker `private-ai-net`), nu expus în afară.
- Serviciul rulează stateless, fără volume, fără credentials.
- Upload-urile trăiesc într-un `tempfile.TemporaryDirectory()` — se șterg imediat după procesare.
- Nici o dată nu părăsește serverul (spre deosebire de LiteLLM care trimite prompt-uri la Vertex AI, tool-urile CAD sunt 100% locale).

---

## 📊 Performanță aproximativă

Măsurat pe ai-hub-server (2 CPU, 6 GB RAM):

| Operație | DWG 10 MB | DWG 100 MB | DWG 500 MB |
|---|---|---|---|
| `/introspect` | ~2 s | ~15 s | ~90 s |
| `/extract` (128 parcele) | ~3 s | ~20 s | ~2 min |
| `/export-excel` | +1 s peste extract | +1 s | +1 s |
| `/reconcile` (128 vs XLSX 128 rânduri) | ~4 s | ~22 s | ~2 min |

Bottleneck-ul principal e conversia DWG→DXF. Fișiere DXF ASCII sunt de 3-5× mai rapide.

### Cum să accesezi și să descarci fișierele 
Tool-urile exportează un link de forma `[⬇️ nume_fisier_areas_m2.xlsx](/api/v1/files/UUID/content)`.
- Fă pur și simplu click pe link pentru a descărca direct fișierul.
- (Informațiile tehnice de export cu base64 au fost înlocuite cu stocare persistenta locală nativă Open WebUI, fiind rezolvat eroarea cu halucinarea modelelor).

### Cum să accesezi și să descarci fișierele
Tool-urile exportează un link de forma `[⬇️ nume_fisier_areas_m2.xlsx](/api/v1/files/UUID/content)`.
- Fă pur și simplu click pe link pentru a descărca direct fișierul.
- (Informațiile tehnice de export cu base64 au fost înlocuite cu stocare persistenta locală nativă Open WebUI, fiind rezolvat eroarea cu halucinarea modelelor).
