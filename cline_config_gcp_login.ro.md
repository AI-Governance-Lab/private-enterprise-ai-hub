# Ghid Configurare Google Cloud & Vertex AI pentru Cline

Acest document descrie configurarea prin care **Service Account-ul dedicat Vertex AI** este folosit **exclusiv în VS Code / Cline**, menținând contul de utilizator `developer@your-org.com` ca implicit (*default*) în Google Cloud CLI (`gcloud`).

---

## 🟢 Status Configurare: ACTIVĂ & TESTATĂ CU SUCCES (Merge 100% ✅)

* **Autentificare SA Vertex AI:** **CONFIRMATĂ ȘI VALIDĂ** (Token generat cu succes pe proiectul `your-gcp-project-id`).
* **Cont CLI activ pe sistem:** `developer@your-org.com` (Neschimbat).
* **Service Account ca default global:** **DEZACTIVAT** (Variabila globală a fost ștearsă din `~/.bashrc`).
* **Izolare:** Completă. Doar procesul VS Code / Cline primește cheia Service Account-ului.

---

## 📌 Detalii Tehnice

| Parametru | Valoare |
| :--- | :--- |
| **Cale cheie Service Account (izolat)** | `/path/to/your/vertex-sa-credentials.json` |
| **Service Account Name** | `vertex-ai-sa@your-gcp-project-id.iam.gserviceaccount.com` |
| **GCP Project ID** | `your-gcp-project-id` |
| **GCP Region** | `us-central1` |
| **Cont implicit CLI (`gcloud`)** | `developer@your-org.com` |

---

## 🚀 Cum pornești VS Code cu Cline (Opțiunea A - Implementată)

### Metoda 1: Folosind alias-ul dedicat (Recomandat)

Am configurat alias-urile în `~/.bashrc`:

```bash
# Open the private-enterprise-ai-hub project directly with Vertex AI credentials
code-cline

# OR open any other directory with Vertex AI credentials
code-vertex /path/to/folder
```

### Metoda 2: Comandă inline directă

```bash
GOOGLE_APPLICATION_CREDENTIALS="${GCP_CREDENTIALS_FILE:-/path/to/your/vertex-sa-credentials.json}" code /opt/private-enterprise-ai-hub
```

---

## ⚙️ Configurare în Setările Cline (VS Code)

Când ai deschis VS Code prin una din comenzile de mai sus:

1. Click pe **⚙️ Settings** din panoul Cline.
2. Setează **API Provider:** `Google Vertex AI`.
3. Completează:
   * **GCP Project ID:** `your-gcp-project-id`
   * **GCP Region:** `us-central1`
   * **Model:** `gemini-2.5-pro` (sau `gemini-2.0-flash` / `gemini-1.5-pro`)
4. Cline se va autentifica automat folosind cheia SA transmisă la pornire, fără să mai ceară vreodată logare în browser.

---

## 🔒 De ce funcționează această abordare?

1. **Fără conflicte în terminal:** Când deschizi un terminal normal pe server, `gcloud` folosește în continuare contul tău `developer@your-org.com`.
2. **Fără expirare token:** Cheia RSA a Service Account-ului este permanentă și nu expiră după câteva ore.
3. **Fără poluare de mediu:** Variabila `GOOGLE_APPLICATION_CREDENTIALS` există **numai** în interiorul arborelui de procese VS Code.

---

## 🔍 Verificare rapidă a funcționării

Pentru a verifica dacă SA-ul generează token-uri valide pe Vertex AI:

```bash
python3 -c "
from google.oauth2 import service_account
from google.auth.transport.requests import Request

creds = service_account.Credentials.from_service_account_file(
    '${GCP_CREDENTIALS_FILE:-/path/to/your/vertex-sa-credentials.json}',
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)
creds.refresh(Request())
print('Autentificare reusita:', bool(creds.token))
print('Proiect conectat:', creds.project_id)
"
```
*(Testul rulează și întoarce: `Autentificare reusita: True`, `Proiect conectat: your-gcp-project-id`)*.


---

## 🌐 Utilizare în VS Code Web (`code-server` pe Portul 9080)

Dacă folosești VS Code rulat direct pe server prin `code-server` (accesibil din browser la `http://<IP_SERVER>:9080` conform [vscode.md](vscode.md)):

### 1. Trebuie restart după instalarea Cline în code-server?
* **Serverul Linux:** **NU**, serverul nu se restartează.
* **Browser / VS Code:** De regulă extensia este activă imediat. Dacă iconița Cline nu apare în bara stângă, este suficient un simplu **refresh de pagină** (`F5` sau `Ctrl+R`) sau `Ctrl+Shift+P` ➡️ **`Developer: Reload Window`**.
* Doar dacă extensia dă erori de memorie sau procese blocate:
  ```bash
  sudo systemctl restart code-server@root
  ```

### 2. Opțiuni de conectare în Cline pe code-server:

#### Opțiunea A: Prin LiteLLM Local (Recomandat)
* Panoul Cline ➡️ **⚙️ Settings**
* **API Provider:** `OpenAI Compatible`
* **Base URL:** `http://localhost:4000/v1`
* **API Key:** `dummy`
* **Model ID:** `Gemini 3.8 Flash` sau `Gemini 3.1 Pro Preview`

#### Opțiunea B: Direct prin Google Cloud Vertex AI
* Panoul Cline ➡️ **⚙️ Settings**
* **API Provider:** `Google Vertex AI`
* **GCP Project ID:** `your-gcp-project-id`
* **GCP Region:** `us-central1`
* **Model:** `gemini-2.5-pro` (sau `gemini-2.0-flash`)
* Cheia SA `/path/to/your/vertex-sa-credentials.json` este deja prezentă pe sistem și validată.

