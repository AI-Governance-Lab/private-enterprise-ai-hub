[English](CAD_README.md) | [Română](CAD_README.ro.md) | [Français](CAD_README.fr.md)

---

# CAD Service — DWG/DXF ⇄ XLSX for Road Expropriations 🛣️📐

Optional module added on top of the main stack ([README.md](README.md)) that extracts surfaces (parcels) from an AutoCAD drawing, generates XLSX files, and checks consistency against the reference cadastral table.

It is installed and started via the same `run.sh`. If the build or startup fails, **the rest of the stack continues to run** — see [Fail-safe design](#fail-safe-design) below.

---

## 🎯 What it does

Three core workflows, driven from chat via Gemini Pro/Flash:

1. **Discovers** what is inside the DWG (`cad_introspect`) — the model receives the list of layers and block attributes, then asks you "which are the parcel layers?" and "which Excel column is the key?". Nothing is hardcoded.
2. **Extracts** surfaces (`cad_extract`, `cad_to_excel`) — areas calculated in m² / ha / km², with totals. You can receive the result as JSON in chat or as a downloadable XLSX file.
3. **Verifies** (`cad_reconcile`) — compares DWG areas with a reference XLSX; outputs a report with differences exceeding tolerance, missing parcels, and ghost parcels.

Supported formats: **`.dwg`** (AutoCAD 2018+ tested via libredwg; upgrade to ODA File Converter if you have problematic files — see below) and **`.dxf`** (ASCII or binary).

---

## 🏗️ Architecture


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


- `cad-service` container on the `private-ai-net` network (not exposed externally — has no published port).
- Communicates only via internal DNS: `http://cad-service:8090`.
- Stateless: no persistent volume, holds no data.
- Python tools run inside the Open WebUI process and make HTTP requests to `cad-service`.

---

## 📁 Added files


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


`run.sh` has been extended with an optional section (enabled by default) that builds the image locally and starts the container.

---

## 🚀 Deploy

### First-time (container is added to an existing stack)


```bash
cd /opt/private-enterprise-ai-hub
./run.sh
```


The script:
1. runs `docker build -t cad-service:local cad-service/`
2. starts the container on the `private-ai-net` network
3. at the end displays `CAD service status: up | build_failed | start_failed | skipped`

### Disabling

If you want to skip it temporarily:


```bash
CAD_SERVICE_ENABLED=0 ./run.sh
```


### Rebuild after code changes


```bash
docker build -t cad-service:local /opt/private-enterprise-ai-hub/cad-service/
docker rm -f cad-service
./run.sh
```


### Import tool into Open WebUI (one-time setup)

1. Open `http://localhost:8080`
2. Workspace → **Tools** → **Import from file**
3. Upload `openwebui-tools/cad_tool.py`
4. Enable the tool for the **Gemini Pro** and/or **AI Assistant Flash** models:
   Admin → Models → *Model* → Tools → check `CAD Tools`

---## 📤 How the User Uploads Files

The model **does not receive URLs or file IDs** — Open WebUI automatically injects the special `__files__` kwarg into tools when files are attached to the message. The CAD tools select the files themselves based on extension (`.dwg`/`.dxf` for drawing, `.xlsx` for reference).

**User steps:**

1. In the chat, attach files to the message using 📎 (Attach):
   - For extract/introspect/to-excel: a single `.dwg` or `.dxf`.
   - For reconcile: **both** — `.dwg` (or `.dxf`) and `.xlsx` — on the **same** message.
2. In the message, write what you want (e.g., "scan the layers" or "verify the areas against the Excel").
3. The model calls the appropriate tool without requiring file IDs or URLs.

**Accepted files:**
- Open WebUI accepts any extension by default (`RAG_ALLOWED_FILE_EXTENSIONS=[]`, no size limit).
- Files are saved on the RAID array at `/mnt/raid1/podman-volumes/open-webui-data/uploads/{uuid}_{filename}` — persistent across restarts.

**Recommendation for large CAD files:**
- Upon upload, click on the file → toggle **"Bypass Embedding and Retrieval"** → ON. This prevents Open WebUI from attempting RAG indexing on CAD binaries (which makes no sense and would pollute the vector DB with raw bytes). The CAD tool has direct access to the file on disk regardless of this setting.

**When the user uploads only one of the 2 expected files:**

The model receives a structured error message, not an exception:

```json
{
  "error": "missing_files",
  "action": "reconcile",
  "need": ["an .xlsx reference table"],
  "attached_now": ["km_12+300.dwg"],
  "hint": "Ask the user to attach both files to the same chat message."
}
```

The model asks the user for the missing file in the conversation language.

---

## 🧪 Post-Deploy Verification


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


If `status` is `degraded`, the DWG converter is not responding — only DXF works until resolved (see troubleshooting).

---

## 🔌 API — Endpoints

All using `multipart/form-data` payload. Internal port **8090** (not exposed externally).

### `GET /health`

Health check + versions.

### `POST /introspect`

**Form:** `file: UploadFile`

**Response (excerpt):**

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
- `layers` = `"*"` (comma-separated glob, e.g., `"S_EXPROPRIERE_*,PARCELA_*"`)
- `source_types` = `"block_attr,hatch,lwpolyline_closed,polyline_closed"` — which entity types
- `unit` = `"m2" | "ha" | "km2"`

Response: JSON with `areas[]`, `total_area`, `count`.

### `POST /export-excel`

Same input as `/extract` + `sheet_name`. Response: **XLSX** file with `Content-Disposition: attachment`.

### `POST /reconcile`

**Form:**
- `dwg: UploadFile`
- `xlsx: UploadFile`
- `xlsx_key_column` — key column name in XLSX (e.g., `Nr_parcela`)
- `xlsx_area_column` — area column (e.g., `Suprafata_masurata_mp`)
- `dwg_key_attribute` — block attribute tag holding the parcel ID (e.g., `NR_PARCELA`)
- `layers`, `source_types`, `unit` (same as in extract)
- `xlsx_sheet` (optional; blank = active sheet)
- `tolerance_pct` (default `0.5`)
- `tolerance_abs` (default `0.01`)

Response: totals, counts, `matched_ok`, `matched_diff` (exceeding tolerance), `missing_in_dwg`, `missing_in_xlsx`. Lists are capped at 200 rows.

---

## 💬 What a Typical Chat Flow Looks Like


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


---## 🛡️ Fail-safe design

**What happens if `cad-service` is down:**

1. `run.sh` displays `CAD service status: build_failed` or `start_failed`, but **the rest of the stack starts normally**.
2. When the model calls a CAD tool, it receives a clear JSON error:
   
```json
   {
     "error": "cad_service_unavailable",
     "action": "introspect",
     "detail": "ConnectError: [Errno -2] Name or service not known",
     "hint": "Restul chat-ului funcționează. Verifică: docker ps | grep cad-service"
   }
   ```

3. The model will tell the user "the CAD service is not responding right now" and continue normally with the rest of the queries (chat, RAG, web search, Vertex AI).

**How to check the status:**

```bash
docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep cad
docker logs cad-service --tail 50
```


---

## 🚨 Troubleshooting

### `CAD service status: build_failed`
- **Cause:** apt/pip failed or build context is missing
- **Check:** `cat /tmp/cad-build.log | tail -50`
- **Common fix:** run `docker system prune -f` to free up space, then re-run `./run.sh`

### `CAD service status: start_failed`
- **Cause:** the internal port is in use or the image failed to build
- **Check:** `cat /tmp/cad-run.log`

### `converter_ok: false` in /health
- **Cause:** `dwg2dxf` (libredwg) is missing from the image
- **Fix:** rebuild image — `docker build -t cad-service:local cad-service/`

### `500 DWG->DXF conversion failed`
- **Cause:** newer DWG file format (AC1032 / AC1035) that libredwg cannot read
- **Quick fix:** save from AutoCAD as ASCII DXF or as DWG 2013 and retry
- **Permanent fix:** upgrade to ODA File Converter (below)

### Areas are incorrect (too large or too small)
- **Cause:** DWG model units are not as expected. Romanian cadastre is usually in meters, but some work in mm.
- **Check:** `/introspect` response contains `insunits_code` and `unit_label`. If it is `mm` (`insunits_code=4`), scaling is performed automatically.
- **If it is `unspecified` (code=0)**, the service assumes meters. Correct this by saving the DWG with `INSUNITS` set.

### `413 File too large`
- **Cause:** file > 500 MB
- **Fix:** override on deploy: in `run.sh` change `-e MAX_UPLOAD_MB=500` to the desired value and redeploy

### CAD tool does not appear in chat
- Verify that you imported it from the UI (Workspace → Tools) — it is not done automatically
- Verify that it is enabled for the model in use (Admin → Models → *Model* → Tools)

### Tool responds with `no_matching_file_attached`
- **Cause:** you entered the command but did not attach the file (or attached it with the wrong extension).
- **Fix:** click on 📎 in the message bar and add the `.dwg` / `.dxf` (or `.xlsx` for reconcile). Resend the message.

### Tool responds with `file_not_on_disk`
- **Cause:** WebUI registered the file_id, but the expected path (`/app/backend/data/uploads/{id}_{name}`) does not exist.
- **Fix:** check the container volume: `docker exec open-webui ls /app/backend/data/uploads/ | grep <id>`. If missing, re-upload it (the upload likely partially failed).

### RAG seems "polluted" after CAD file upload
- **Cause:** Open WebUI by default routes any upload through Tika for RAG. ASCII DXF can generate raw coordinate chunks.
- **Fix:** during upload, click on the CAD file → enable **"Bypass Embedding and Retrieval"**. The CAD tool works regardless — it does not depend on RAG.### `cad-service` unreachable or resolution error from Open WebUI (`Temporary failure in name resolution`)
- **Cause:** Reloading the host firewall (`firewall-cmd --reload`) reset Podman's dynamic rules (`netavark`), blocking DNS queries on `10.89.0.1:53`.
- **Fix:** The Podman network was added to the firewall's `trusted` zone, and the `netavark-firewalld-reload.service` service was permanently enabled. See the dedicated troubleshooting section in [vscode.md](vscode.md).

---

## ⬆️ Upgrade to ODA File Converter (recommended for DWG 2018+)

libredwg works on most DWGs, but lags behind very new formats. ODA File Converter (Open Design Alliance, free, closed-source) is the industry standard.

**Steps:**

1. Download the `.deb` for Linux x86_64 from:
   <https://www.opendesign.com/guestfiles/oda_file_converter>
   (requires free registration)
2. Place the file in `cad-service/` (e.g.: `ODAFileConverter_QT6_lnxX64_8.3dll_25.3.deb`)
3. Uncomment the block in `cad-service/Dockerfile`:
   
```dockerfile
   COPY ODAFileConverter_*.deb /tmp/oda.deb
   RUN apt-get update && apt-get install -y --no-install-recommends /tmp/oda.deb \
       xvfb libglu1-mesa && rm -rf /var/lib/apt/lists/* /tmp/oda.deb
   ```

4. Modify `app.py` → the `_convert_dwg_to_dxf` function to call `ODAFileConverter` instead of `dwg2dxf`
5. Rebuild + redeploy: `docker build -t cad-service:local cad-service/ && docker rm -f cad-service && ./run.sh`

---

## 🔒 Security & isolation

- Port 8090 is **internal only** (Docker network `private-ai-net`), not exposed externally.
- The service runs stateless, without volumes, without credentials.
- Uploads live in a `tempfile.TemporaryDirectory()` — they are deleted immediately after processing.
- No data leaves the server (unlike LiteLLM which sends prompts to Vertex AI, CAD tools are 100% local).

---

## 📊 Approximate performance

Measured on ai-hub-server (2 CPU, 6 GB RAM):

| Operation | DWG 10 MB | DWG 100 MB | DWG 500 MB |
|---|---|---|---|
| `/introspect` | ~2 s | ~15 s | ~90 s |
| `/extract` (128 parcels) | ~3 s | ~20 s | ~2 min |
| `/export-excel` | +1 s over extract | +1 s | +1 s |
| `/reconcile` (128 vs XLSX 128 rows) | ~4 s | ~22 s | ~2 min |

The main bottleneck is the DWG→DXF conversion. ASCII DXF files are 3–5× faster.

### How to access and download files 
Tools export a link of the form `[⬇️ filename_areas_m2.xlsx](/api/v1/files/UUID/content)`.
- Simply click on the link to download the file directly.
- (Technical base64 export details were replaced with native Open WebUI local persistent storage, fixing the model hallucination error).

### How to access and download files
Tools export a link of the form `[⬇️ filename_areas_m2.xlsx](/api/v1/files/UUID/content)`.
- Simply click on the link to download the file directly.
- (Technical base64 export details were replaced with native Open WebUI local persistent storage, fixing the model hallucination error).