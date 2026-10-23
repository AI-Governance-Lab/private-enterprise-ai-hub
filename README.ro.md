[English](README.md) | [Română](README.ro.md) | [Français](README.fr.md)

---

# Private Enterprise AI Hub 🏢🤖

Un asistent AI complet, self-hosted, care utilizează **Open WebUI**, **LiteLLM** și **Google Vertex AI (Gemini 3.8 Flash + Gemini 3.1 Pro Preview)**. Proiectat pentru scalabilitate la nivel enterprise și confidențialitate prin transferarea procesării LLM în Google Cloud, păstrând în același timp toate datele sensibile, documentele și istoricul conversațiilor în întregime sub controlul dumneavoastră, pe propria infrastructură.

## 🚀 Caracteristici principale

- **💬 Interfață web modernă:** UI similar cu ChatGPT prin Open WebUI
- **🌐 Căutare web în timp real:** Căutare integrată pe internet folosind DuckDuckGo (Open WebUI) + Google Search grounding (LiteLLM/Vertex AI)
- **📚 RAG local (Retrieval-Augmented Generation):** Încărcați fișiere PDF și documente; AI-ul le caută și le citează utilizând **Google text-embedding-004** (bazat pe cloud, fără consum de resurse CPU locale)
- **💾 Istoric complet al conversațiilor:** Toate conversațiile sunt salvate local pe RAID 1; complet privat
- **🤖 Hub multi-model (Google Vertex AI + Mistral AI):** 
  - **Codestral (codestral-2508)** (Codestral 2508) — specializat pentru programare, refactorizare, FIM, context de 256k (Roo Code / Cline / Open WebUI)
  - **Gemini 3.1 Pro Preview** (Gemini 3.1 Pro Preview) — raționament avansat, interogări complexe
  - **Gemini 3.8 Flash** (Gemini 3.8 Flash) — răspunsuri instantanee, 1-3 secunde, ideal pentru utilizare zilnică
  - **Ministral 14B** (Ministral 14B) — model AI european rapid, pentru uz general
  - *Detalii complete și ghid de configurare IDE: [litellm.md](litellm.ro.md)*
- **📄 Procesare inteligentă PDF:** OCR automat prin Apache Tika (PDF-uri scanate, imagini din documente)
- **📐 Reconciliere CAD & XLSX (opțional):** Extrageți suprafețe din fișiere AutoCAD `.dwg`/`.dxf`, exportați în Excel, reconciliați cu tabele de referință cadastrală — conceput pentru fluxurile de lucru de expropriere a drumurilor. Consultați [CAD_README.md](CAD_README.ro.md).
- **👥🔐 Izolare multi-utilizator:** Fiecare utilizator își vede doar propriile fișiere; panou de administrare pentru configurare
- **🚀 Pornire automată:** Serviciul systemd asigură repornirea containerelor după reboot-ul serverului
- **🔐 Autentificare securizată:** Acreditări GCP Service Account; nicio cheie API nu este stocată în cod
- **🐳 Bazat pe Docker:** Implementare ușoară; totul rulează în containere

---

## 📋 Ce conține (Actualizat în octombrie 2026)

### Versiuni fixate curente

| Component | Image / Package | Tag / Version | Notes |
|-----------|-----------------|---------------|-------|
| **Open WebUI** | `ghcr.io/open-webui/open-webui` | `v0.12.3` | Versiune stabilă fixată (Port 8080) |
| **LiteLLM** | `ghcr.io/berriai/litellm` | `main-latest` | Tag de tip rolling (actualizare automată la pull, Port 4000) |
| **Apache Tika** | `docker.io/apache/tika` | `latest` | Tag de tip rolling (actualizare automată la pull, Port 9998) |
| **code-server (VS Code)** | Native RPM (`coder/code-server`) | `v4.137.0+` | Web IDE + Cline AI (Port 9080) |

Consultați secțiunea [Version Management & Upgrades](#-version-management--upgrades) de mai jos pentru fluxul complet de lucru necesar modificării acestor versiuni.### Componente noi adăugate

**Modele Multi-LLM:**
- **Codestral (codestral-2508)** (Codestral 2508) — Model specializat de programare (context 256k), agent AI pentru IDE (Roo Code / Cline)
- **Gemini 3.1 Pro Preview** (Gemini 3.1 Pro Preview) — Raționament profund, probleme complexe, generare de cod
- **Gemini 3.8 Flash** (Gemini 3.8 Flash) — Răspunsuri instantanee (1-3 sec), căutare web, chat zilnic
- **Ministral 14B** (Ministral 14B) — LLM european rapid pentru raționament general și chat multilingv

**Procesare inteligentă a documentelor:**
- **Apache Tika** — OCR și extragere de text din PDF-uri scanate, imagini și documente complexe
- **Google text-embedding-004** — Embeddings bazate pe cloud (768 dimensiuni), înlocuiesc modelele locale solicitante pentru CPU
  - Fără blocarea CPU-ului în timpul încărcării documentelor
  - Căutare semantică mai rapidă și mai precisă

**Gestionare multi-utilizator:**
- **Utilizator admin** — Acces complet la configurarea sistemului și la fișierele tuturor utilizatorilor
- **Utilizatori obișnuiți** — Văd doar fișierele proprii; nu pot accesa documentele altor utilizatori
- **Partajarea modelelor în spațiul de lucru** — Toți utilizatorii pot vedea și utiliza modelele LLM disponibile

**Fiabilitate a sistemului și rețea:**
- **Pornire automată prin systemd** — Containerele repornesc automat după repornirea serverului
- **Cheie de sesiune fixă** — Sesiunile de browser rămân valide după reporniri
- **Stocare RAID 1** — 3,7 TB spațiu de stocare redundant pentru istoricul de chat și documente
- **Netavark Firewall Sync** — Sincronizare automată a firewall-ului prin systemd (`netavark-firewalld-reload.service`), asigurând funcționarea continuă a DNS-ului pentru containerele Podman după reîncărcările de firewall

**Dezvoltare și programare la distanță:**
- **VS Code Server (code-server)** — IDE în browser pe portul 9080 pentru dezvoltare la distanță de pe orice dispozitiv (telefon, laptop)
- **Agent AI Cline** — Agent AI de programare integrat în VS Code, care se conectează la LiteLLM sau Google Vertex AI (consultați [vscode.md](vscode.md))

---

##  Gestionarea versiunilor și upgrade-uri

Toate tagurile imaginilor de containere sunt declarate ca variabile la începutul fișierului [run.sh](run.sh). Pentru a modifica orice versiune, editați acele variabile și rulați din nou scriptul.

### Unde sunt fixate versiunile

`run.sh` (liniile 13–15):


```bash
OPEN_WEBUI_IMAGE="ghcr.io/open-webui/open-webui:v0.11.3"
LITELLM_IMAGE="ghcr.io/berriai/litellm:main-latest"
TIKA_IMAGE="docker.io/apache/tika:latest"
```


`run.sh` apelează întotdeauna `docker pull` pentru fiecare imagine înainte de a recrea containerele, astfel încât o reluare a execuției cu variabile neschimbate actualizează tagurile mobile (`main-latest`, `latest`), iar o reluare cu o versiune incrementată pentru `OPEN_WEBUI_IMAGE` descarcă și implementează noua versiune fixată.

### Istoricul versiunilor Open WebUI în această implementare

| Dată | De la → La | Note |
|------|-----------|-------|
| 2026-09-06 | `main` (0.11.0) → `v0.11.3` | Fixat la versiunea stabilă. Rezolvă un bug de migrare a bazei de date din 0.11.0–0.11.2. |

### Cum se face upgrade la o versiune mai nouă de Open WebUI

1. Verificați cea mai recentă versiune stabilă: <https://github.com/open-webui/open-webui/releases>
2. Citiți notele de lansare (release notes) pentru modificări incompatibile (breaking changes) și avertismente privind migrarea bazei de date.
3. **Faceți backup volumului de date** (consultați [Backup & Restore](#-backup--restore) mai jos).
4. Editați `run.sh` și schimbați tagul pe linia `OPEN_WEBUI_IMAGE`:
   
```bash
   OPEN_WEBUI_IMAGE="ghcr.io/open-webui/open-webui:v0.11.4"
   ```

5. Reimplementați: `./run.sh`
6. Verificați (consultați [Verificare post-implementare](#post-deploy-verification)).

### Semantica tagurilor

| Tag | Semnificație | Utilizare recomandată |
|-----|--------------|-----------------------|
| `vX.Y.Z` | Versiune stabilă fixată (ex. `v0.11.3`) | ✅ Utilizare în producție / enterprise. Reproductibil. |
| `latest` | Întotdeauna cea mai recentă versiune stabilă | Urmărire automată a versiunii stabile; mai puțin predictibil. |
| `main` | Ramură de dezvoltare de ultimă oră (bleeding edge) | Nu este recomandat; poate include commit-uri defecte. |

---## 🚀 Moduri de deploy & flux de lucru pentru redeploy

Trei operațiuni suportate, toate gestionate prin același `run.sh`.

### Modul 1 — Primul deploy (instalare curată)

Cerințe preliminare: `docker` sau `podman` instalat, fișierul JSON pentru GCP Service Account pregătit, montarea RAID disponibilă la `/mnt/raid1` (sau editați calea `RAID_STORAGE` în `run.sh`).


```bash
git clone <this-repo> /opt/private-ai-hub
cd /opt/private-ai-hub

# 1. Place your GCP credentials
cp /path/to/service-account-key.json ./${GCP_CREDENTIALS_FILE:-credentials.json}
chmod 600 credentials.json

# (Optional) If you want to use a different filename for your credentials, 
# you can configure it via a .env file:
# echo "GCP_CREDENTIALS_FILE=${GCP_CREDENTIALS_FILE:-my-custom-key.json}" > .env

# 2. Edit litellm_config.yaml with your GCP project ID
$EDITOR litellm_config.yaml

# 3. Deploy
chmod +x run.sh
./run.sh

# 4. (Recommended) Enable systemd autostart — see "Auto-Start Containers" below
```


Deschideți http://localhost:8080, creați contul de administrator.

### Modul 2 — Redeploy (configurație neschimbată, reîmprospătare imagini / restart)

Utilizați această opțiune după modificarea `litellm_config.yaml`, după o repornire a sistemului sau pentru a prelua actualizările rolling-tag pentru LiteLLM/Tika.


```bash
cd /opt/private-ai-hub
./run.sh
```


`run.sh` este idempotent: execută `docker rm -f` pe containerele existente și le recreează. Datele de pe volumul RAID rămân neatinse.

### Modul 3 — Upgrade Open WebUI la o versiune nouă

Consultați [Cum se face upgrade la Open WebUI](#how-to-upgrade-open-webui-to-a-newer-release) de mai sus. TL;DR:


```bash
# 1. Backup
STAMP=$(date +%Y%m%d-%H%M%S)
tar -czf /mnt/raid1/podman-volumes/backups/open-webui-data-pre-upgrade-$STAMP.tar.gz \
  -C /mnt/raid1/podman-volumes open-webui-data

# 2. Edit run.sh → bump OPEN_WEBUI_IMAGE tag
$EDITOR run.sh

# 3. Redeploy
./run.sh

# 4. Verify (see below)
```


### Verificare post-deploy

Fiecare deploy ar trebui să se încheie cu aceste 4 verificări:


```bash
# a) All 3 containers up
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'

# b) Open WebUI version matches the pinned tag
docker exec open-webui cat /app/package.json | grep '"version"'

# c) HTTP endpoint healthy
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://localhost:8080/health

# d) DB migrations ran cleanly (no errors/traceback)
docker logs open-webui 2>&1 | grep -iE 'error|traceback|alembic' | tail -20
```


Rezultat așteptat: 3 containere `Up`, versiunea corespunde cu eticheta `OPEN_WEBUI_IMAGE`, HTTP 200, fără erori/traceback-uri.

### Rollback

Dacă upgrade-ul afectează funcționarea aplicației:


```bash
# 1. Stop containers
docker stop open-webui litellm tika

# 2. Restore the pre-upgrade backup
rm -rf /mnt/raid1/podman-volumes/open-webui-data
tar -xzf /mnt/raid1/podman-volumes/backups/open-webui-data-pre-upgrade-<STAMP>.tar.gz \
  -C /mnt/raid1/podman-volumes

# 3. Revert OPEN_WEBUI_IMAGE in run.sh to the previous tag, then redeploy
$EDITOR run.sh
./run.sh
```


---

## 💾 Backup & Restore

Toate datele persistente se află în `/mnt/raid1/podman-volumes/open-webui-data` (baza de date SQLite, fișiere încărcate, vector DB, cache). LiteLLM și Tika sunt stateless.

**Backup (sigur de rulat în timp ce containerele sunt active, dar snapshot-urile consistente necesită oprirea acestora):**


```bash
STAMP=$(date +%Y%m%d-%H%M%S)
docker stop open-webui   # optional but recommended for a consistent snapshot
tar -czf /mnt/raid1/podman-volumes/backups/open-webui-data-$STAMP.tar.gz \
  -C /mnt/raid1/podman-volumes open-webui-data
docker start open-webui
```


**Restaurare:**


```bash
docker stop open-webui
rm -rf /mnt/raid1/podman-volumes/open-webui-data
tar -xzf /mnt/raid1/podman-volumes/backups/open-webui-data-<STAMP>.tar.gz \
  -C /mnt/raid1/podman-volumes
docker start open-webui
```


**Rotația backup-urilor** (păstrează ultimele 5, rulat prin cron):


```bash
ls -1t /mnt/raid1/podman-volumes/backups/open-webui-data-*.tar.gz | tail -n +6 | xargs -r rm
```


---

## 📋 Procesul de deployment (Ce face `run.sh`)


```
┌──────────────────────────────────────────────────────────┐
│        ./run.sh   (Start Script)                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. Load Configuration                                  │
│     ├─ Read: credentials.json (GCP Service Account)     │
│     ├─ Read: litellm_config.yaml (Model routing)        │
│     └─ Set: RAID_STORAGE path                           │
│                                                          │
│  2. Prepare Network & Storage                           │
│     ├─ Create Docker network: private-ai-net            │
│     ├─ Create directories                               │
│     └─ Check RAID availability                          │
│                                                          │
│  3. Start LiteLLM Container                             │
│     ├─ Image: ghcr.io/berriai/litellm:main-latest       │
│     ├─ Mount: credentials.json (read-only)              │
│     ├─ Mount: litellm_config.yaml (read-only)           │
│     ├─ Port: 4000 (internal only)                       │
│     └─ Network: private-ai-net                          │
│                                                          │
│  4. Start Open WebUI Container                          │
│     ├─ Image: ghcr.io/open-webui/open-webui:v0.11.3     │
│     ├─ Mount: /mnt/raid1/.../open-webui-data (RW)       │
│     ├─ Port: 8080 (exposed to browser)                  │
│     ├─ Env: OPENAI_API_BASE=http://litellm:4000         │
│     └─ Network: private-ai-net                          │
│                                                          │
│  5. Done! Access at http://localhost:8080               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```


---

## 🏗️ Prezentare generală a arhitecturii


```
┌─────────────────────────────────────────────────────┐
│                     User Browser                      │
│              http://localhost:8080                    │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼ (HTTP)
         ┌───────────────────────────┐
         │   Open WebUI Container    │
         │  (Port 8080, Internal)    │
         │                           │
         │ • Web UI Interface        │
         │ • Chat Management         │
         │ • Document Upload & RAG   │
         │ • Web Search (DuckDuckGo) │
         │ • Persistent Volume       │
         └──────────┬────────────────┘
                    │
        ┌───────────┴──────────┐
        │ (OpenAI-compatible   │
        │  API calls)          │
        ▼                      ▼
    ┌───────────────────────────────────┐
    │  LiteLLM Proxy Container          │
    │ (Port 4000, Internal)             │
    │                                   │
    │ • OpenAI ↔ Vertex AI Translation  │
    │ • Tool Management                 │
    │ • Request Processing              │
    │ • Credentials Handling            │
    └──────────┬───────────────────────┘
               │
       ┌───────┴──────────┐
       │ (Vertex AI API   │
       │  + gRPC)         │
       ▼                  ▼
    ┌──────────────────────────────────┐
    │  Google Cloud (External)         │
    │  Vertex AI - Gemini 3.8 + 3.1 Pro │
    │                                  │
    │ • LLM Inference                  │
    │ • Google Search Grounding        │
    │ • Token Processing               │
    └──────────────────────────────────┘
```


### Fluxul de date

1. **Interogarea utilizatorului** → Browserul trimite mesajul către Open WebUI
2. **Procesare** → Open WebUI verifică dacă este necesară o căutare web
   - Dacă este necesar: interoghează DuckDuckGo
   - Formatează contextul pentru AI
3. **Apel API** → Open WebUI trimite o cerere compatibilă cu OpenAI către LiteLLM (portul 4000)
4. **Translatare** → LiteLLM convertește formatul OpenAI în formatul Google Vertex AI
   - Adaugă instrumentul Google Search dacă este configurat
   - Include credențialele (service account JSON) prin ${GCP_CREDENTIALS_FILE:-credentials.json}
5. **Procesare LLM** → Vertex AI (Gemini 3.8 Flash sau Gemini 3.1 Pro Preview)
   - Opțional caută pe internet (prin Google Search grounding)
   - Generează răspunsul
6. **Răspuns** → Returnat prin LiteLLM → Open WebUI → Browser
7. **Stocare** → Istoricul conversațiilor este salvat local (persistă între reporniri)

### Detalii despre containerele Docker


```
┌─────────────────────────────────────────────────────────────────┐
│                    Podman Network: private-ai-net               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐ │
│  │   open-webui Container   │  │   litellm Container      │ │
│  ├──────────────────────────┤  ├──────────────────────────┤ │
│  │ Image: open-webui/       │  │ Image: berriai/          │ │
│  │        open-webui:v0.11.3│  │        litellm:main-lat. │ │
│  │                          │  │                          │ │
│  │ Ports:                   │  │ Ports:                   │ │
│  │  8080:8080 (browser)     │  │  4000:4000 (internal)    │ │
│  │  ↓                       │  │  ↑                       │ │
│  │  (OpenAI API calls)      │←─→│ (Convert to Vertex AI)  │ │
│  │                          │  │                          │ │
│  │ Env:                     │  │ Env: VERTEX_PROJECT      │ │
│  │  OPENAI_API_BASE=        │  │      GCP credentials     │ │
│  │  http://litellm:4000     │  │ Models:                  │ │
│  │  RAG_EMBEDDING_ENGINE=   │  │  • Gemini 3.1 Pro Preview      │ │
│  │  RAG_EMBEDDING_MODEL=    │  │  • Gemini 3.8 Flash        │ │
│  │  text-embedding-004      │  │  • text-embedding-004    │ │
│  │  CONTENT_EXTRACTION_     │  │                          │ │
│  │  ENGINE=tika             │  │ Volumes:                 │ │
│  │                          │  │  credentials.json (RO)   │ │
│  │ Volumes:                 │  │  litellm_config.yaml(RO) │ │
│  │  /mnt/raid1/podman-      │  │  (stateless)             │ │
│  │   volumes/open-webui-    │  │                          │ │
│  │   data:/app/backend/data │  │                          │ │
│  │                          │  │                          │ │
│  │ Database:                │  │                          │ │
│  │  webui.db (SQLite)       │  │                          │ │
│  │  ├─ Users & Accounts     │  │                          │ │
│  │  ├─ Chat History         │  │                          │ │
│  │  ├─ Uploaded Files       │  │                          │ │
│  │  └─ Vector Embeddings    │  │                          │ │
│  │                          │  │                          │ │
│  └──────────────────────────┘  └──────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────┐                                 │
│  │   tika Container         │                                 │
│  ├──────────────────────────┤                                 │
│  │ Image: apache/tika:latest                                 │
│  │                          │                                 │
│  │ Port: 9998 (internal)    │                                 │
│  │  ↑                       │                                 │
│  │  (PDF extraction, OCR)   │                                 │
│  │                          │                                 │
│  │ Purpose:                 │                                 │
│  │  • Extract text from     │                                 │
│  │    scanned PDFs          │                                 │
│  │  • Process images        │                                 │
│  │  • Handle complex docs   │                                 │
│  │                          │                                 │
│  │ (stateless)              │                                 │
│  └──────────────────────────┘
│
│  ┌──────────────────────────────────────────────────────────┐
│  │              Storage: RAID 1 Mount Point                │
│  │           /mnt/raid1/podman-volumes/open-webui-data    │
│  ├──────────────────────────────────────────────────────────┤
│  │  Filesystem: /dev/md0 → XFS                             │
│  │  Size: 3.7 TB | Used: 521 GB | Available: 3.2 TB       │
│  │  Protection: RAID 1 (mirrored, redundant)              │
│  │                                                         │
│  │  Contents:                                              │
│  │   ├─ webui.db → Chat history, users, files             │
│  │   ├─ uploads/ → User-uploaded documents                │
│  │   ├─ vector_db/ → Embeddings for RAG                   │
│  │   └─ cache/ → Temporary files & model cache            │
│  │                                                         │
│  │  ✅ Persists across container restarts                 │
│  │  ✅ Redundancy protection                              │
│  │  ✅ Plenty of space for large document collections     │
│  │                                                         │
│  └──────────────────────────────────────────────────────────┘
│
└─────────────────────────────────────────────────────────────────┘

External Connections:
├─ Browser (localhost:8080) ─→ Open WebUI (HTTP)
├─ Open WebUI ─→ LiteLLM (internal Docker network)
├─ LiteLLM ─→ Google Vertex AI (HTTPS/gRPC to Google Cloud)
└─ DuckDuckGo/Web ← Open WebUI (for web search results)
```


**Comunicarea între containere:**
- Open WebUI comunică cu LiteLLM prin rețeaua internă Docker (portul 4000)
- Doar portul 8080 este expus către browser
- Portul 4000 este ascuns din exterior; nu este accesibil din internet
- Toate cererile urmează traseul: Browser → Open WebUI → LiteLLM → Vertex AI

---

## 🛠️ Instrucțiuni de configurare

### Cerințe preliminare

- Docker & Docker Compose (sau Podman)
- Proiect GCP cu Vertex AI activat
- Fișier cu credențiale Service Account JSON (implicit: credentials.json, suprascriere prin GCP_CREDENTIALS_FILE în .env)
- Sistem Linux cu Podman/Docker
- Cel puțin 8 GB RAM (recomandat 16 GB+ pentru indexarea documentelor mari)
- Opțional: Stocare externă RAID/NAS pentru documente### 1. Configurare credențiale GCP

1. Accesați [Google Cloud Console](https://console.cloud.google.com/)
2. Creați sau selectați proiectul dvs. GCP
3. Activați Vertex AI API
4. Creați un Service Account:
   - IAM & Admin → Service Accounts
   - Create service account
   - Atribuiți rolul: "Vertex AI User"
5. Creați o cheie JSON și descărcați-o
6. **Salvați cheia ca `${GCP_CREDENTIALS_FILE:-credentials.json}` în directorul rădăcină al acestui proiect** (sau specificați numele acesteia prin `GCP_CREDENTIALS_FILE` într-un fișier `.env`).

### 2. Configurare LiteLLM cu modele

Editați `litellm_config.yaml`:


```yaml
model_list:
  # Main model for complex reasoning
  - model_name: Gemini 3.1 Pro Preview
    litellm_params:
      model: vertex_ai/gemini-3.1-pro-preview
      vertex_project: "your-gcp-project-id"  # ← Replace with your project ID
      vertex_location: "global"
      tools:
        - googleSearch: {}  # Enables Google Search grounding
      system_prompt: "Ești asistentul familiei. Ajuți la orice, bun la toate, despre casă, familie, școală, informații generale, programare, teme. Ai acces la Google Search și poți căuta informații actuale de pe internet în timp real."

  # Fast model for daily use
  - model_name: Gemini 3.8 Flash
    litellm_params:
      model: vertex_ai/gemini-3.8-flash
      vertex_project: "your-gcp-project-id"  # ← Replace with your project ID
      vertex_location: "global"
      tools:
        - googleSearch: {}
      system_prompt: "Ești asistentul familiei. Ajuți la orice, bun la toate, despre casă, familie, școală, informații generale, programare, teme. Ai acces la Google Search și poți căuta informații actuale de pe internet în timp real."

  # Embedding model for RAG (replaces local model)
  - model_name: text-embedding-004
    litellm_params:
      model: vertex_ai/text-embedding-004
      vertex_project: "your-gcp-project-id"  # ← Replace with your project ID
      vertex_location: "global"
```


**Ghid de selecție a modelelor:**
- **Gemini 3.1 Pro Preview** → Interogări complexe, code debugging, analiză aprofundată (timp de răspuns 5-30 sec)
- **Gemini 3.8 Flash** → Răspunsuri rapide, căutare web, chat zilnic (timp de răspuns 1-3 sec)
- **Artist (Google Imagen 3)** → Generare de imagini de înaltă calitate cu Google Imagen 2 (model: `imagen@005`)
- **text-embedding-004** → Utilizat automat pentru embedding-uri RAG (nu este necesară selectarea manuală)

### 3. (Opțional) Configurare stocare pe NAS/RAID

Dacă dispuneți de stocare externă NAS sau RAID (de ex., `/mnt/raid1`), scriptul `run.sh` stochează automat datele RAG acolo:


```bash
# Default: /mnt/raid1/podman-volumes/open-webui-data
# If path doesn't exist, create it:
mkdir -p /mnt/raid1/podman-volumes/open-webui-data

# run.sh will use this automatically
./run.sh

# Verify storage:
ls -la /mnt/raid1/podman-volumes/open-webui-data/
```


**Avantajele stocării externe:**
- ✅ Separă datele de discul de sistem
- ✅ Protecție RAID pentru istoricul de chat
- ✅ Backup-uri mai ușoare
- ✅ Mai mult spațiu pentru colecții mari de documente

**Editați run.sh pentru a utiliza o cale personalizată:**

```bash
# Modify this line in run.sh:
RAID_STORAGE="${DATA_STORAGE_PATH:-/mnt/raid1/podman-volumes/open-webui-data}"  # ← Change path
```


### 4. Deploy


```bash
# Make the deployment script executable
chmod +x run.sh

# Run the deployment
./run.sh
```


Aceasta va:
- Crea rețeaua Docker `private-ai-net`
- Porni proxy-ul LiteLLM (portul 4000, intern)
- Porni motorul OCR Tika (portul 9998, intern)
- Porni Open WebUI (portul 8080, accesibil)
- Monta stocarea persistentă pentru istoricul de chat
- Instala RapidOCR pentru extragere îmbunătățită a imaginilor (opțional)

### 5. (Recomandat) Pornire automată a containerelor la reboot-ul serverului

Creați un serviciu systemd pentru a porni automat containerele după reboot:

**Creați `/etc/systemd/system/private-ai.service`:**

```ini
[Unit]
Description=Private AI Service (Open WebUI + LiteLLM + Tika)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
WorkingDirectory=/opt/private-ai-hub
ExecStart=/opt/private-ai-hub/run.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```


**Activați serviciul:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable private-ai.service
sudo systemctl start private-ai.service

# Verify status
sudo systemctl status private-ai.service
docker ps  # Should show all 3 containers running
```


**Acum containerele vor porni automat după reboot-ul sistemului!**

### 6. Accesarea aplicației

Deschideți browserul și navigați la:

```
http://localhost:8080
```


**Configurare inițială:**
- Creați un cont de admin (stocat local, criptat)
- Selectați fie "Gemini 3.1 Pro Preview" (calitate mai bună), fie "Gemini 3.8 Flash" (mai rapid)
- Începeți conversația!

---

## 🔧 Variabile de mediu și configurare

### Configurare Open WebUI (setată în run.sh)


```bash
# Authentication - IMPORTANT: Fixed key prevents session loss on restart
WEBUI_SECRET_KEY=replace_with_a_secure_random_string

# RAG/Embedding Configuration
RAG_EMBEDDING_ENGINE=openai              # Use OpenAI-compatible endpoint (LiteLLM)
RAG_EMBEDDING_MODEL=text-embedding-004   # GCP text-embedding-004 (768 dimensions)
RAG_OPENAI_API_BASE_URL=http://litellm:4000/v1

# PDF Processing
CONTENT_EXTRACTION_ENGINE=tika            # Use Apache Tika for OCR
TIKA_SERVER_URL=http://tika:9998         # Tika server (internal Docker network)
RAG_PDF_EXTRACT_IMAGES=False              # Disabled: avoids slow local RapidOCR
# Note: The Admin Panel setting for "Content Extraction Engine" overrides this.

# LLM Configuration
OPENAI_API_BASE_URL=http://litellm:4000/v1  # LiteLLM proxy endpoint
```


**Puncte cheie:**
- `WEBUI_SECRET_KEY` este fixă → sesiunile persistă între restarturi ✅
- `text-embedding-004` utilizează Google Cloud (fără consum pe CPU local) → embedding-uri rapide ✅
- `CONTENT_EXTRACTION_ENGINE=tika` → OCR automat pentru PDF-uri scanate ✅
- `RAG_PDF_EXTRACT_IMAGES=False` → ignoră RapidOCR local lent; Tika gestionează imaginile ✅

### Configurare LiteLLM (litellm_config.yaml)

3 modele configurate:
1. **Gemini 3.1 Pro Preview** - Gemini 3.1 Pro Preview (analiză complexă)
2. **Gemini 3.8 Flash** - Gemini 3.8 Flash (răspunsuri rapide)
3. **text-embedding-004** - GCP embeddings pentru RAG

Toate modelele au Google Search grounding activat.

---

## 💻 Cum funcționează### Chat cu Web Search

1. **Activare Web Search:** Faceți clic pe butonul de căutare din Open WebUI înainte de a adresa întrebarea
2. **Interogare Open WebUI → DuckDuckGo:** Caută pe web folosind DuckDuckGo
3. **Context transmis către LLM:** Rezultatele căutării sunt incluse în prompt
4. **Răspuns LLM:** Gemini 3.8 Flash (sau 3.1 Pro Preview) generează un răspuns cu citări

### Vertex AI Google Search Grounding

În plus, ambele modele Gemini au acces la **grounding cu Google Search** configurat în LiteLLM:
- Când LiteLLM trimite cereri, include parametrul `tools: [googleSearch: {}]`
- Vertex AI poate căuta autonom pe Google dacă consideră necesar
- Oferă informații în timp real și verificarea faptelor

### Local Document RAG

1. **Încărcare document:** Clic pe „Upload” în Open WebUI; selectați fișierul PDF sau text
2. **Procesare:** Documentul este extras (text sau OCR dacă este scanat) prin Tika
3. **Embedding:** Google text-embedding-004 creează vectori cu 768 de dimensiuni
4. **Căutare în chat:** Faceți referire la document după nume în interogare
5. **Acces AI:** LLM-ul primește bucăți din document (document chunks) drept context
6. **Citări:** Răspunsurile includ sursa de proveniență a informațiilor

#### Pipeline de procesare PDF (cu Tika OCR)

**Tipuri de PDF-uri gestionate:**
- ✅ **PDF-uri bazate pe text** (căutabile) → Tika extrage textul direct
- ✅ **PDF-uri scanate** (imagini) → Tika rulează OCR pentru a extrage textul
- ✅ **PDF-uri mixte** (text + imagini) → Tika procesează toate straturile
- ✅ **Formate complexe** (pe mai multe coloane, tabele) → Tika gestionează layout-ul

**Pași de procesare:**

```
1. User uploads: "scanned_document.pdf" (e.g., scan of a book)
   ↓
2. Open WebUI sends to Tika server
   CONTENT_EXTRACTION_ENGINE=tika
   TIKA_SERVER_URL=http://tika:9998
   ↓
3. Tika container processes PDF:
   - Detects if text or scanned image
   - Runs OCR on image sections
   - Extracts text with original layout preserved
   ↓
4. Text returned to Open WebUI
   ↓
5. Split into chunks (~1000 tokens each, 100 token overlap)
   ↓
6. Each chunk embedded using Google text-embedding-004:
   - 768-dimensional dense vectors
   - Cloud-based (fast, no local CPU)
   - Returns in <1 second per batch
   ↓
7. Embeddings + original text stored in SQLite
   ↓
8. File saved to persistent volume (RAID storage)
```


#### Cum funcționează căutarea RAG (pas cu pas)

**Faza 2: Interogare și recuperare (Query & Retrieval)**

```
1. User asks: "Cât e timeout-ul pentru API calls?"
   ↓
2. Open WebUI embeds the query (same model)
   ↓
3. Semantic search: Find top 3 most similar chunks
   (using cosine similarity on embeddings)
   ↓
4. Retrieve original text from those chunks
   ↓
5. Build context:
   "# Relevant Documents
   <source id="1">company_handbook.pdf (page 5)
   Timeout for API calls is set to 300 seconds...
   </source>"
   ↓
6. Append context to user prompt
   ↓
7. Send to LLM with full context
```


**Faza 3: Răspuns LLM**

```
LLM sees:
- System prompt
- Full chat history
- **Document context (from RAG)**
- User question

LLM generates response + citations:
"According to the handbook, the timeout is 300 seconds [1]."
         ↑ Citation points back to document chunk
```


---

## 📂 Stocare fișiere și locații

### În interiorul volumelor Docker

**Volumul open-webui-data:**

```
/app/backend/data/
├── webui.db                    # SQLite database (chat history, users)
├── uploads/                    # Uploaded files
│   ├── company_handbook.pdf
│   ├── project_doc.txt
│   └── ...
└── embeddings/                 # Stored embeddings (cache)
    ├── embedding_vectors.db
    └── ...
```


**Pe mașina gazdă (Host):**

```bash
# Find where Docker stores the volume
docker volume inspect open-webui-data
# Output shows: "Mountpoint": "/var/lib/docker/volumes/open-webui-data/_data"

# View uploaded files (as root)
sudo ls -la /var/lib/docker/volumes/open-webui-data/_data/uploads/

# Extract a file (example: backup)
sudo cp /var/lib/docker/volumes/open-webui-data/_data/uploads/file.pdf ~/backup/
```


### Schema bazei de date (tabele relevante)


```sql
-- Files table
CREATE TABLE file (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  filename TEXT,
  file_path TEXT,
  file_size INTEGER,
  created_at INTEGER
);

-- File chunks (after splitting)
CREATE TABLE document (
  id TEXT PRIMARY KEY,
  file_id TEXT,
  file_name TEXT,
  title TEXT,
  content TEXT,           -- The actual chunk text
  embedding BLOB,         -- Vector embedding (binary)
  metadata JSON
);

-- Chat messages (includes document references)
CREATE TABLE chat_message (
  id TEXT PRIMARY KEY,
  chat_id TEXT,
  role TEXT,
  content TEXT,           -- Message text
  files JSON,             -- Referenced files
  citations JSON          -- Document sources
);
```


### Cum să accesați fișierele programatic

**În interiorul containerului:**

```bash
docker exec open-webui ls -la /app/backend/data/uploads/
```


**Backup pentru toate fișierele încărcate:**

```bash
docker run --rm -v open-webui-data:/data \
  -v ~/backup:/backup \
  alpine cp -r /data/uploads/ /backup/
```


**Interogarea directă a embedding-urilor:**

```bash
docker exec open-webui sqlite3 /app/backend/data/webui.db \
  "SELECT file_name, content FROM document LIMIT 5;"
```


---

## 🔍 Utilizarea RAG în practică

### Exemplu: Documente interne ale companiei

**Configurare:**
1. Încărcați: `policies.pdf`, `org_chart.xlsx`, `procedures.md`
2. Open WebUI le indexează automat

**Interogarea utilizatorului:**

```
"What's the vacation policy?"
```


**În culise:**

```
Query embedding ↓
Search for similar chunks in policies.pdf
Found: "Vacation Policy section (page 3)"
Chunk content: "Employees get 20 days + national holidays..."

Final prompt to LLM:
---
System: You are a helpful assistant...
Context from documents:
[1] policies.pdf: "Vacation Policy... 20 days..."
[2] org_chart.xlsx: "Company structure..."
---
User: "What's the vacation policy?"
---
```


**Răspuns LLM:**

```
According to company policy, employees receive 20 days of vacation 
annually, plus national holidays [1]. Contact HR for exceptions [1].
```


### Avansat: Căutare pe mai multe documente

**Încărcare fișiere:**
- `Q1_Report.pdf`
- `Q2_Report.pdf`
- `Budget_2026.xlsx`

**Interogare:** „Care a fost evoluția veniturilor de la Q1 la Q2?”

**RAG extrage:** Automat secțiunile relevante atât din raportul Q1, cât și din Q2

---

## ⚙️ Configurare RAG (Setări de administrare)

Accesibil prin panoul de administrare Open WebUI:


```
Settings → Retrieval → RAG Configuration
```


**Configurația curentă (folosind GCP text-embedding-004):**

```yaml
rag:
  chunk_size: 1000              # Tokens per chunk
  chunk_overlap: 100            # Token overlap between chunks
  top_k: 3                       # Retrieve top 3 matching chunks
  relevance_threshold: 0         # Minimum similarity score (0 = no filter)
  
  embedding_model: text-embedding-004           # GCP embeddings
  embedding_engine: openai                      # OpenAI-compatible (via LiteLLM)
  openai_api_base: http://litellm:4000/v1      # LiteLLM proxy
  
  enable_hybrid_search: false    # BM25 + semantic (if enabled)
  full_context: false            # Use all chunks or just top_k
  
  content_extraction_engine: tika              # PDF OCR
  tika_server_url: http://tika:9998            # Tika server
```


**Sfaturi de optimizare:**
- **PDF-urile scanate eșuează?** Verificați dacă Tika rulează: `docker logs tika`
- **Generarea de embeddings este lentă?** Verificați conectivitatea GCP: `docker logs litellm | grep "text-embedding-004"`
- **Documente mari?** Măriți `chunk_size` (de ex., 2000)
- **Prea multe rezultate?** Micșorați `top_k` (de ex., 2)
- **Lipsesc informații relevante?** Micșorați `relevance_threshold`

---## 🚀 Limitări RAG & Soluții alternative

| Problemă | Cauză | Soluție alternativă |
|----------|-------|---------------------|
| "Document not found" | Fișierul nu a fost încărcat sau referința este greșită | Încărcați fișierul, apoi referențiați-l după numele exact al fișierului |
| Textul din PDF-ul scanat este gol | PDF-ul este de tip imagine, OCR-ul Tika a eșuat | Verificați log-urile Tika: `docker logs tika` |
| PDF-ul criptat este respins | PDF-ul este protejat prin parolă | Decriptați local mai întâi: `qpdf --decrypt input.pdf output.pdf` |
| Rezultate irelevante | Segmentare deficitară a chunk-urilor sau relevanță scăzută | Împărțiți manual documentul, încărcați-l ca fișiere separate |
| Căutare lentă | Latență de rețea către GCP (text-embedding-004) | Normal; embedding-urile durează 1-2 secunde per batch |
| Pierdere date după repornire | Volumul nu este persistent | Utilizați întotdeauna volume montate (implicit în run.sh) |
| Extragerea PDF este goală | Serverul Tika nu rulează sau s-a oprit neașteptat | Reporniți: `docker restart tika` |

---

## 📊 Stocare & Performanță

**Utilizare spațiu pe disc:**
- Open WebUI de bază: ~500 MB
- Per fișier încărcat: de 1-10x dimensiunea fișierului (metadata + embeddings)
- Index SQLite: ~100 MB per 1000 de documente
- Stocare RAID: 3,7 TB disponibili (la `/mnt/raid1`)

**Performanță embedding (cu GCP text-embedding-004):**
- Generare embeddings: 1-2 secunde (bazat pe cloud, nu necesită CPU local)
- Căutare prin similitudine: 50-500ms (SQLite full scan)
- Preluare context document: <100ms
- **Avantaj:** Descarcă sarcina de calcul a embedding-urilor; eliberează CPU-ul local pentru alte activități

**Performanță interogare:**
- Cu Gemini 3.1 Pro Preview: 5-30 secunde (raționament complex)
- Cu Gemini 3.8 Flash: 1-3 secunde (răspunsuri rapide)

**Optimizare:**

```bash
# Rebuild indexes (if database gets slow)
docker exec open-webui sqlite3 /app/backend/data/webui.db \
  "VACUUM; ANALYZE;"

# Check database size
docker exec open-webui du -sh /app/backend/data/webui.db

# Monitor storage usage
docker exec open-webui du -sh /app/backend/data/uploads/
docker exec open-webui du -sh /app/backend/data/vector_db/
```


---

## 🔄 Bune practici RAG

### Izolarea fișierelor multi-utilizator

**Model de securitate:**

Fiecare fișier încărcat este etichetat cu `user_id`:

```sql
file table:
  id: 88f922e4-..., user_id: user_a, filename: budget.pdf
  id: 92g033f5-..., user_id: user_b, filename: roadmap.docx

document table (RAG):
  collection_name: ..., user_id: user_a, content: "Budget Q1..."
  collection_name: ..., user_id: user_b, content: "Roadmap 2026..."
```


**Izolare impusă:**
- ✅ Utilizatorul A interoghează `/api/retrieval/files/` → Primește doar fișierele Utilizatorului A
- ✅ Utilizatorul B interoghează `/api/retrieval/files/` → Primește doar fișierele Utilizatorului B
- ✅ UI-ul ascunde documentele celorlalți utilizatori
- ✅ Contextul RAG include doar documentele utilizatorului curent

**Model de amenințări:**

| Scenariu | Risc | Măsură de atenuare |
|----------|------|--------------------|
| Utilizatorul A accesează UI-ul | Redus | Izolarea fișierelor la nivel de API |
| Adminul accesează SQLite | Ridicat | Adminul are acces complet la baza de date |
| Cineva obține token-ul de admin | Ridicat | Rotiți parola imediat |
| SQL injection în Open WebUI | Mediu | Remediat în cele mai recente versiuni |

**Bune practici:**
- Mențineți o parolă de admin puternică
- Nu partajați contul de admin
- Rulați Open WebUI în spatele unui auth proxy dacă este expus la internet
- Monitorizați permisiunile fișierului SQLite: `sudo ls -la /var/lib/docker/volumes/open-webui-data/_data/webui.db`## 🔍 Modele: "Gemini 3.1 Pro Preview" & "Gemini 3.8 Flash"

Ambele modele sunt configurate cu același system prompt:

**System Prompt:**
> "Ești asistentul familiei. Ajuți la orice, bun la toate, despre casă, familie, școală, informații generale, programare, teme.
> 
> Ai acces la Google Search și poți căuta informații actuale de pe internet în timp real. Când cineva te întreabă despre știri, vreme, prețuri, evenimente recente sau orice informații care se pot schimba, folosește Google Search pentru a oferi răspunsuri corecte și actualizate."

**Când se utilizează:**
- **Gemini 3.1 Pro Preview** — Probleme complexe, debugging de cod, cercetare, când ai nevoie de raționament profund (deep reasoning)
- **Gemini 3.8 Flash** — Întrebări zilnice, răspunsuri rapide, căutare pe web, chat pe documente

**Capabilități (ambele modele):**
- Căutare web (DuckDuckGo + Google Search grounding)
- Upload de fișiere & RAG (cu GCP text-embedding-004)
- Vision (înțelegerea imaginilor)
- Interpretare de cod
- Informații în timp real

---

## 📁 Structura proiectului


```
.
├── README.md                 # This file
├── CAD_README.md             # Optional CAD service (DWG/DXF + XLSX reconciliation)
├── ${GCP_CREDENTIALS_FILE:-credentials.json}          # GCP Service Account key (default, can be overridden via .env)
├── .env                      # (Optional) Define GCP_CREDENTIALS_FILE=your-key.json
├── litellm_config.yaml       # LiteLLM model configuration
├── run.sh                    # Deployment script
├── cad-service/              # Optional CAD extraction container (see CAD_README.md)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
└── openwebui-tools/          # Python tools for manual import into Open WebUI
    └── cad_tool.py
```


---

## 🚨 Depanare (Troubleshooting)

### "Error: Tool 'search' not found"
- **Cauză:** Căutarea web nu a fost configurată în Open WebUI
- **Rezolvare:** Admin panel → Settings → Web Search → Activați DuckDuckGo

### "Connection refused on port 4000"
- **Cauză:** Containerul LiteLLM nu a putut porni
- **Verificare:** `docker logs litellm`
- **Problemă frecventă:** Fișierul `credentials.json` lipsește sau este invalid (sau fișierul configurat prin `.env`)

### "Cannot access Vertex AI"
- **Cauză:** Permisiunile pentru Service Account sau proiectul GCP nu sunt configurate corect
- **Rezolvare:**
  - Verificați dacă `${GCP_CREDENTIALS_FILE:-credentials.json}` (sau fișierul personalizat de credențiale) se află în rădăcina proiectului
  - Asigurați-vă că Service Account-ul are rolul "Vertex AI User" (pentru `${GCP_CREDENTIALS_FILE:-credentials.json}`)
  - Verificați dacă ID-ul proiectului GCP corespunde cu cel din `litellm_config.yaml`

### "Chat history not persisting"
- **Cauză:** Volumul Open WebUI nu este montat corect
- **Rezolvare:** Verificați montarea RAID: `ls -la /mnt/raid1/podman-volumes/open-webui-data/`
- Dacă este gol, reporniți cu `./run.sh`

### "PDF upload takes too long / times out"
- **Cauză:** Serverul Tika nu răspunde sau procesul OCR procesează un document de mari dimensiuni
- **Verificare:** 
  
```bash
  docker logs tika  # See OCR progress
  docker ps | grep tika  # Verify container is running
  ```

- **Rezolvare:** Acordați mai mult timp serverului Tika (se inițializează la primul PDF)
- **Dacă Tika se blochează (crashes):** `docker logs tika -f` pentru a vedea eroarea detaliată

### "PDF upload is very slow and CPU usage is high"
- **Cauză:** Open WebUI folosește motorul implicit `RapidOCR` în loc de `Tika`. Acest lucru se poate întâmpla dacă setarea din Admin Panel este incorectă.
- **Rezolvare:**
  1. Mergeți la **Admin Panel** -> **Settings** -> **Retrieval**.
  2. Găsiți setarea **Content Extraction Engine**.
  3. Schimbați-o din `default` în `Tika` și salvați.

### "PDF content appears empty after upload"
- **Cauze:**
   1. **PDF criptat:** Tika nu poate extrage date din fișiere PDF protejate cu parolă
   2. **Format complex:** Scanat la o rezoluție neobișnuită
   3. **Tika nu rulează:** Containerul nu a putut porni
- **Rezolvare pentru PDF-uri criptate:**
  
```bash
  # Decrypt locally first using qpdf
  qpdf --decrypt --password-is-hex-string=XXXXXXXX input.pdf output.pdf
  # Then upload output.pdf
  ```

- **Verificați dacă Tika funcționează:**
  
```bash
  docker exec tika curl -s http://localhost:9998/version
  # Should return Tika version info
  ```


### "Embedding API errors or slow embeddings"
- **Cauză:** Endpoint-ul Google text-embedding-004 nu poate fi accesat
- **Verificare:**
  
```bash
  docker logs open-webui | grep "embedding"
  ```

- **Rezolvare:**
  - Verificați dacă credențialele GCP sunt valide
  - Verificați variabila de mediu `RAG_EMBEDDING_MODEL=text-embedding-004`
  - Asigurați-vă că LiteLLM poate accesa Google Cloud (conectivitate de rețea)### "Containerele nu pornesc la restart (boot server)"
- **Cauza:** Podman ignoră `--restart unless-stopped` la boot (spre deosebire de Docker)
- **Fix aplicat:** Systemd service `private-ai.service` creat și activat
- **Verificare:**
  
```bash
  systemctl status private-ai.service   # Trebuie: enabled + active
  systemctl is-enabled private-ai.service  # Trebuie: enabled
  ```

- **Repornire manuală dacă e nevoie:**
  
```bash
  systemctl start private-ai.service
  # sau
  ./run.sh
  ```


### "Sesiune invalidată după repornirea containerului"
- **Cauză:** Cheia de sesiune s-a schimbat la restart
- **Status:** ✅ **REZOLVAT** — WEBUI_SECRET_KEY este acum setat fix în run.sh
- **Verificare:** Sesiunile ar trebui să persiste între repornirile `./run.sh`
- **Notă:** Dacă folosiți un fișier custom de credențiale, asigurați-vă că `${GCP_CREDENTIALS_FILE:-credentials.json}` este montat corespunzător

### "Open WebUI arată în continuare versiunea veche după upgrade"
- **Cauza 1:** Noul tag de imagine nu a fost descărcat efectiv (problemă temporară de rețea, cache).
- **Cauza 2:** Containerul nu a fost recreat (doar repornit).
- **Fix:**
  
```bash
  docker pull ghcr.io/open-webui/open-webui:<new-tag>
  docker rm -f open-webui
  ./run.sh
  docker exec open-webui cat /app/package.json | grep '"version"'
  ```


### "`docker pull` se blochează la final pe imagini mari (runtime podman)"
- **Cauză:** Podman se blochează ocazional după „Writing manifest to image destination” pentru imagini de mai mulți GB.
- **Fix:** Anulați cu Ctrl-C și reîncercați aceeași comandă `docker pull` direct (în afara `run.sh`). Odată ce imaginea este prezentă local, rulați din nou `./run.sh`.

### "Migrarea bazei de date a eșuat / aplicația nu pornește după upgrade"
- **Cauză:** Migrare Alembic omisă sau coruptă între versiunile Open WebUI.
- **Fix:**
  1. Verificați logurile pentru migrarea eșuată: `docker logs open-webui 2>&1 | grep -iE 'alembic|migration|error'`
  2. Restabiliți backup-ul de dinaintea upgrade-ului (vezi [Rollback](#rollback)).
  3. Raportați eroarea de migrare upstream dacă aceasta se reproduce pe o instanță curată.

### "Open WebUI: Server Connection Error / Model not found"
- **Cauză:** După o comandă `firewall-cmd --reload` (de exemplu la deschiderea de porturi pe server), `firewalld` pe CentOS Stream 9 resetează regulile dinamice Netavark. Interfața `podman1` și subnetul containerelor `10.89.0.0/24` ajung sub zona implicită `public`, care blochează portul 53 (DNS intern `aardvark-dns` pe `10.89.0.1:53`). În log-urile `open-webui` apare:
  
```text
  Cannot connect to host litellm:4000 [Temporary failure in name resolution]
  Model '' was not found
  ```

- **Fix aplicat definitiv:**
  1. Adăugarea rețelei containerelor în zona `trusted`:
     
```bash
     sudo firewall-cmd --zone=trusted --add-interface=podman1 --permanent
     sudo firewall-cmd --zone=trusted --add-source=10.89.0.0/24 --permanent
     sudo firewall-cmd --reload
     ```

  2. Activarea serviciului oficial de sincronizare automată Netavark la evenimente de reload ale firewall-ului:
     
```bash
     sudo systemctl enable --now netavark-firewalld-reload.service
     ```

  3. Repornirea containerului WebUI: `podman restart open-webui` (sau `./run.sh`).

### "Conflict de port 8080 (VS Code / code-server și Open WebUI)"
- **Cauză:** Atât Open WebUI cât și `code-server` folosesc în mod implicit portul 8080.
- **Fix:** `code-server` a fost configurat pe portul `9080` în `~/.config/code-server/config.yaml` (`bind-addr: 0.0.0.0:9080`), portul 9080 a fost deschis în firewall, iar serviciul a fost repornit cu `sudo systemctl restart code-server@root`. Vezi ghidul complet în [vscode.md](vscode.md).

---

##  Gestionarea utilizatorilor și controlul accesului

### Crearea și gestionarea utilizatorilor

**Utilizator Admin (Acces complet):**
- Poate accesa setările de sistem
- Poate vedea fișierele și istoricul de chat ale tuturor utilizatorilor
- Poate configura modelele LLM și setările RAG
- Poate gestiona conturile și rolurile de utilizator

**Utilizatori obișnuiți (Izolarea fișierelor):**
- Pot vedea doar propriile documente încărcate
- Pot vizualiza doar propriul istoric de chat
- Pot accesa toate modelele LLM disponibile (Gemini 3.1 Pro Preview + Flash)
- **Nu pot vedea sau accesa fișierele altor utilizatori**### Configurarea mai multor utilizatori

1. **Primul utilizator = Admin:**
   
```bash
   Open WebUI → Create account → Auto-becomes admin
   Example: marian.ropota@gmail.com
   ```


2. **Adăugarea de utilizatori suplimentari:**
   
```bash
   Admin panel → Settings → Users → Add User
   They are automatically "regular users" (non-admin)
   ```


3. **Verificarea rolului utilizatorului (prin baza de date):**
   
```bash
   docker exec open-webui python3 -c "
   import sqlite3
   conn = sqlite3.connect('/app/backend/data/webui.db')
   cur = conn.cursor()
   cur.execute('SELECT email, role FROM user')
   for row in cur.fetchall():
       print(f'{row[0]} → {row[1]}')
   conn.close()
   "
   ```


4. **Schimbarea rolului unui utilizator (dacă este necesar):**
   
```bash
   # Make user an admin
   docker exec open-webui python3 -c "
   import sqlite3
   conn = sqlite3.connect('/app/backend/data/webui.db')
   conn.execute(\"UPDATE user SET role='admin' WHERE email='user@example.com'\")
   conn.commit()
   conn.close()
   "
   ```


### Izolarea fișierelor în baza de date

**Cum funcționează:**
- Fiecare utilizator are un `user_id` unic în SQLite
- Toate fișierele încărcate sunt etichetate cu `user_id`
- Interogările RAG sunt filtrate după `user_id`
- Istoricul conversațiilor este filtrat după `user_id`

**Exemplu:**

```sql
-- When admin queries database
SELECT filename FROM file WHERE user_id = 123  -- All of user 123's files

-- When user 123 queries
SELECT filename FROM file WHERE user_id = 123  -- Only their files (auto-filtered)
```


### Partajarea modelelor din workspace între mai mulți utilizatori

Toți utilizatorii pot vedea și utiliza aceleași modele din workspace:
- Gemini 3.1 Pro Preview (pentru analize complexe)
- Gemini 3.8 Flash (pentru chat rapid)
- text-embedding-004 (utilizat automat pentru RAG)

**Configurare:**

```bash
# This setting enables model visibility for all users
docker exec open-webui python3 -c "
import sqlite3, json
conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute(\"UPDATE config SET value=? WHERE key='user.permissions'\", 
            (json.dumps({'workspace': {'models': True}}),))
conn.commit()
conn.close()
"
```


---

## 🔧 Setări Admin

Accesați panoul de administrare prin interfața Open WebUI (pictograma Settings dacă sunteți autentificat ca admin).

**Setări cheie:**
- **Web Search:** Activat (DuckDuckGo)
- **Search Confirmation:** Dezactivat (căutările se efectuează automat)
- **Model Parameters:** Promptul de sistem (system prompt) include disponibilitatea Google Search
- **RAG:** Configurat cu Google text-embedding-004 (embeddings bazate pe cloud)
- **PDF Processing:** Tika OCR activat pentru PDF-uri scanate
- **User Isolation:** Accesul la fișiere este controlat prin rolul utilizatorului
- **Session Persistence:** Cheia fixă WEBUI_SECRET_KEY previne deconectarea la repornire

### Important: Cheie de sesiune fixă

Variabila de mediu `WEBUI_SECRET_KEY` este fixată în `run.sh`:

```bash
WEBUI_SECRET_KEY=replace_with_a_secure_random_string
```


Sesiunile persistă la repornirile `./run.sh` fără a forța reautentificarea.

---

## 🔍 Monitorizare și întreținere

### Verificarea stării containerelor


```bash
docker ps  # Should show open-webui, litellm, tika
```


### Vizualizarea logurilor containerelor


```bash
docker logs open-webui -f     # Open WebUI logs
docker logs litellm -f        # LiteLLM proxy logs
docker logs tika -f           # Tika OCR logs
```


### Verificarea bazei de date și a stocării


```bash
# Database size
docker exec open-webui du -h /app/backend/data/webui.db

# User files storage
docker exec open-webui du -sh /app/backend/data/uploads/

# Vector embeddings storage
docker exec open-webui du -sh /app/backend/data/vector_db/
```


### Repornirea containerelor


```bash
./run.sh                              # Restart all containers
sudo systemctl restart private-ai.service  # Via systemd
```


---

## 📊 Utilizarea resurselor

- **RAM:** ~2 GB (Open WebUI) + overhead de rețea
- **Stocare:** ~5 GB de bază + variabil (istoric conversații, documente)
- **CPU:** Procesare locală minimă (cea mai mare parte a sarcinilor este preluată de Google Cloud)
- **Lățime de bandă:** Depinde de utilizarea LLM-urilor și de căutările web

---

##  Pentru dezvoltatori: Structura și arhitectura proiectului

### Nu este necesar cod personalizat

Acest proiect **nu include cod sursă** — este o **implementare bazată exclusiv pe configurare**:

| Componentă | Rol | Proveniență |
|-----------|------|--------------|
| **run.sh** | Orchestrare containere | Repo-ul dumneavoastră (bash simplu) |
| **litellm_config.yaml** | Configurare LiteLLM | Repo-ul dumneavoastră (YAML) |
| **${GCP_CREDENTIALS_FILE:-credentials.json}** | Autentificare GCP | Proiectul dumneavoastră GCP (JSON) |
| **Open WebUI container** | Imagine pre-construită: `ghcr.io/open-webui/open-webui:v0.11.3` (fixată; editați `run.sh` pentru modificare) | Docker Hub / GHCR |
| **LiteLLM container** | Imagine pre-construită: `ghcr.io/berriai/litellm:main-latest` (rolling) | Docker Hub / GHCR |

**Dumneavoastră furnizați configurația. Imaginile Docker aduc codul precompilat.**

### Ce face fiecare container


```
┌─ open-webui (ghcr.io/open-webui/open-webui:v0.11.3)
│  • React/TypeScript frontend
│  • FastAPI backend
│  • SQLite database (chat history)
│  • RAG pipeline (embeddings, retrieval)
│  • Persistent volume: /app/backend/data
│
└─ litellm (ghcr.io/berriai/litellm:main-latest)
   • FastAPI server (port 4000)
   • OpenAI → Vertex AI protocol converter
   • Credential manager
   • Tool routing (googleSearch, etc.)
   • No persistent data (stateless)
```


### Fluxul de date (tehnic)


```
1. User Query
   Browser → POST http://localhost:8080/api/chat/completions
   
2. Open WebUI Processing
   • Check if web search needed
   • If yes: Query DuckDuckGo (local)
   • Retrieve document context (if RAG enabled)
   • Build system prompt + user message
   
3. LiteLLM Proxy
   POST http://litellm:4000/chat/completions (internal Docker network)
   {
     "model": "gemini-3.8-flash",
     "messages": [...],
     "tools": [{"googleSearch": {}}],  // ← Added by LiteLLM config
     "stream": true
   }
   
4. LiteLLM Translation
   • Load credentials.json
   • Convert OpenAI format → Vertex AI gRPC format
   • Add vertex_project, vertex_location
   • Keep tools parameter
   
5. Vertex AI API Call
   gRPC to: generativelanguage.googleapis.com
   Body includes: tool definitions
   
6. Gemini 3.8 Flash / 3.1 Pro Preview Processing
   • Receives prompt + tools
   • May autonomously call Google Search (grounding)
   • Generates response with citations
   
7. Response Chain
   Vertex AI → LiteLLM → Open WebUI → Browser
   
8. Storage
   • Chat message saved to SQLite (local)
   • Document chunks cached locally
   • No data persisted at Google
```


### Limite de securitate


```
🟢 Local (Your Machine)
├── Chat history (SQLite)
├── Uploaded documents
├── User accounts & auth tokens
├── credentials.json
├── Web search results cache
└── Embedding vectors (local)

🔵 In-Transit (Encrypted)
├── TLS to Vertex AI API
└── Internal Docker network (isolated)

🔴 External (Google Cloud)
├── Prompt + context (in flight only)
└── LLM inference (deleted after response)
     ⚠️ NOT stored by Google
     ⚠️ NOT used for training
     (Check your GCP data retention settings)
```### Detalii cheie de implementare

**Izolarea porturilor:**
- Port 8080: Open WebUI (acesta este cel pe care îl accesezi)
- Port 4000: LiteLLM proxy (doar intern Docker)
- Niciun port nu este expus implicit, cu excepția portului 8080

**Montări de volume (Volume Mounts):**
- `open-webui-data`: Persistă baza de date SQLite + fișierele încărcate
- `litellm_config.yaml`: Read-only, montat în containerul LiteLLM
- `${GCP_CREDENTIALS_FILE:-credentials.json}`: Read-only, montat în containerul LiteLLM

**Variabile de mediu (în interiorul containerului LiteLLM):**

```bash
GOOGLE_APPLICATION_CREDENTIALS=/app/${GCP_CREDENTIALS_FILE:-credentials.json}
# (set by run.sh)
```


**Rețea:**
- `private-ai-net`: Rețea Docker care conectează ambele containere
- Rezoluție DNS: `open-webui:8080` este accesibil din containerul `litellm`
- Fără acces la rețele externe, cu excepția Google Cloud APIs

---

## 👥 Configurare multi-utilizator & Izolarea fișierelor

### Roluri de utilizator


```
┌─────────────────────────────────────────────────────────┐
│               User Role Permissions                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Admin User (marian.ropota@gmail.com)                  │
│  ├─ Full system access                                 │
│  ├─ Can see all users' files and chats                 │
│  ├─ Can configure models, settings, permissions        │
│  └─ Can manage other user accounts                     │
│                                                         │
│  Regular Users (ropota.mihaela.andreea@gmail.com,...)  │
│  ├─ Can only see own uploaded files                    │
│  ├─ Can only see own chat history                      │
│  ├─ Can access all workspace models (Thinker + Flash)  │
│  └─ Cannot see other users' documents or chats         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```


### Detalii privind izolarea

Fișierele fiecărui utilizator sunt etichetate cu `user_id` în SQLite:

```sql
FILE table:  id, user_id, filename, file_path
DOCUMENT table (RAG): content, user_id, embedding
```


**Filtrarea interogărilor RAG:**
- Când un utilizator caută documente, doar documentele proprii sunt transformate în embeddings și extrase
- Fără contaminare încrucișată (cross-contamination) între utilizatori

---

### Clasificarea datelor

| Date | Locație | Expunere | Note |
|------|---------|----------|------|
| Chat History | SQLite local | Niciuna | Doar pe mașina ta |
| Documente | Volum local | Niciuna | Nu sunt încărcate niciodată în cloud |
| Embeddings | Volum local | Niciuna | Generate local |
| Prompt-uri | În tranzit către Google | Minimă | Șterse după răspuns |
| Credențiale | Fișier local | Niciuna | Nu sunt expuse niciodată extern |
| Configurație LiteLLM | Fișier local | Niciuna | Montat read-only |

### Model de amenințări (Threat Model)

**❌ Nu se poate întâmpla:**
- Google să îți acceseze istoricul de chat
- Containerele să trimită date către exterior („phoning home”)
- `credentials.json` să fie expus în loguri
- Datele de chat să persiste în cloud

**⚠️ S-ar putea întâmpla dacă:**
- Expui portul 8080 pe internet fără autentificare
- Faci commit la `credentials.json` în git
- Dai `docker push` containerului către un registru public
- Traficul de rețea nu este criptat

**✅ Atenuat prin:**
- Implementare locală (air-gapped implicit)
- TLS către Google APIs
- Autentificare prin Service account (nu API keys în cod)
- Credențiale montate read-only

### Bune practici

1. **Păstrează credențialele private**
   
```bash
   # Add to .gitignore
   echo "credentials.json" >> .gitignore
   echo ".env" >> .gitignore
   ```


2. **Nu expune portul 8080**
   
```bash
   # ❌ DON'T do this (unless intentional)
   docker run -p 0.0.0.0:8080:8080  # Exposes to internet
   
   # ✅ Default (safe)
   docker run -p 127.0.0.1:8080:8080  # Localhost only
   ```


3. **Monitorizează costurile GCP**
   - Verifică [Vertex AI pricing](https://cloud.google.com/vertex-ai/pricing)
   - Configurează alerte de facturare în consola GCP

4. **Rotește periodic credențialele**
   - Șterge cheile vechi de Service Account
   - Generează altele noi în consola GCP
   - Actualizează `credentials.json`

---

## 📝 Comenzi

**Vezi [🚀 Deploy Modes & Redeploy Workflow](#-deploy-modes--redeploy-workflow) for full first-deploy, redeploy, upgrade, and rollback recipes.** Această secțiune listează comenzile uzuale de zi cu zi.


```bash
# Start / redeploy the application (idempotent)
./run.sh

# View logs
docker logs litellm -f       # LiteLLM proxy
docker logs open-webui -f    # Open WebUI
docker logs tika -f          # Tika OCR

# Stop containers
docker stop open-webui litellm tika

# Restart a single container without full redeploy
docker restart open-webui

# Remove containers (data on RAID stays intact)
docker rm -f open-webui litellm tika

# Check the currently deployed Open WebUI version
docker exec open-webui cat /app/package.json | grep '"version"'

# Clear all data (⚠️ destructive — deletes chat history, users, uploads)
rm -rf /mnt/raid1/podman-volumes/open-webui-data/*
```


### Systemd Autostart (pornire automată la boot)


```bash
# Verificare status service
systemctl status private-ai.service

# Pornire manuală prin systemd
systemctl start private-ai.service

# Oprire prin systemd
systemctl stop private-ai.service

# Activare/dezactivare autostart
systemctl enable private-ai.service
systemctl disable private-ai.service

# Vizualizare loguri systemd
journalctl -u private-ai.service -f
```


### Teste Rapide


```bash
# Test 1: Containere rulează?
docker ps

# Test 2: LiteLLM sănătos?
curl http://localhost:4000/health

# Test 3: Open WebUI accesibil?
curl -o /dev/null -w "%{http_code}" http://localhost:8080
# Trebuie: 200

# Test 4: Date pe RAID?
ls -lh /mnt/raid1/podman-volumes/open-webui-data/

# Test 5: Confirmare RAID în container?
docker exec open-webui df -h /app/backend/data
# Trebuie: /dev/md0 (3.7T)

# Test 6: Network conectat?
docker network inspect private-ai-net --format "{{range .Containers}}{{.Name}} {{end}}"
# Trebuie: litellm open-webui
```


---

## 🌍 Documentație în mai multe limbi

Acest proiect suportă documentație în mai multe limbi:
- **Engleză** (Implicit): `*.md`
- **Română**: `*.ro.md`
- **Franceză**: `*.fr.md`

**Regulă de traducere:** La traducerea documentației, **toate comentariile de cod trebuie să rămână în limba engleză**. Doar textul Markdown înconjurător trebuie tradus.

---##  Pași următori

- Personalizează system prompt-ul în Admin settings
- Încarcă propriile documente pentru RAG
- Explorează diferite interogări pentru a testa web search
- Monitorizează costurile în Google Cloud Console

Bucură-te de asistentul tău AI privat! 🤖

- **16-Sep-2026:** (sau data curentă) Am sincronizat și integrat complet noile tool-uri `CAD Tools (v0.3.0)` pentru suport XLSX cu download curat.

- **06-Sep-2026:** Am sincronizat și integrat complet noile tool-uri `CAD Tools (v0.3.0)` pentru suport XLSX nativ în Open WebUI cu download curat.