[English](cline_config_gcp_login.md) | [Română](cline_config_gcp_login.ro.md) | [Français](cline_config_gcp_login.fr.md)

---

# Google Cloud & Vertex AI Configuration Guide for Cline

This document describes the configuration where the **dedicated Vertex AI Service Account** is used **exclusively in VS Code / Cline**, while keeping the user account `developer@your-org.com` as default in the Google Cloud CLI (`gcloud`).

---

## 🟢 Configuration Status: ACTIVE & SUCCESSFULLY TESTED (100% Working ✅)

* **Vertex AI SA Authentication:** **CONFIRMED AND VALID** (Token successfully generated on project `your-gcp-project-id`).
* **Active CLI Account on System:** `developer@your-org.com` (Unchanged).
* **Service Account as Global Default:** **DISABLED** (The global variable was removed from `~/.bashrc`).
* **Isolation:** Complete. Only the VS Code / Cline process receives the Service Account key.

---

## 📌 Technical Details

| Parameter | Value |
| :--- | :--- |
| **Service Account Key Path (Isolated)** | `/path/to/your/vertex-sa-credentials.json` |
| **Service Account Name** | `vertex-ai-sa@your-gcp-project-id.iam.gserviceaccount.com` |
| **GCP Project ID** | `your-gcp-project-id` |
| **GCP Region** | `us-central1` |
| **Default CLI Account (`gcloud`)** | `developer@your-org.com` |

---

## 🚀 How to Launch VS Code with Cline (Option A - Implemented)

### Method 1: Using the Dedicated Alias (Recommended)

The aliases have been configured in `~/.bashrc`:


```bash
# Open the private-enterprise-ai-hub project directly with Vertex AI credentials
code-cline

# OR open any other directory with Vertex AI credentials
code-vertex /path/to/folder
```


### Method 2: Direct Inline Command


```bash
GOOGLE_APPLICATION_CREDENTIALS="${GCP_CREDENTIALS_FILE:-/path/to/your/vertex-sa-credentials.json}" code /opt/private-enterprise-ai-hub
```


---

## ⚙️ Configuration in Cline Settings (VS Code)

Once you have opened VS Code via one of the commands above:

1. Click on **⚙️ Settings** in the Cline panel.
2. Set **API Provider:** `Google Vertex AI`.
3. Fill in:
   * **GCP Project ID:** `your-gcp-project-id`
   * **GCP Region:** `us-central1`
   * **Model:** `gemini-2.5-pro` (or `gemini-2.0-flash` / `gemini-1.5-pro`)
4. Cline will automatically authenticate using the SA key passed at startup, without ever prompting for a browser login again.

---

## 🔒 Why Does This Approach Work?

1. **No terminal conflicts:** When you open a standard terminal on the server, `gcloud` continues to use your `developer@your-org.com` account.
2. **No token expiration:** The Service Account's RSA key is permanent and does not expire after a few hours.
3. **No environment pollution:** The `GOOGLE_APPLICATION_CREDENTIALS` variable exists **only** within the VS Code process tree.

---

## 🔍 Quick Functionality Check

To verify if the SA generates valid tokens on Vertex AI:


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

*(The test runs and returns: `Autentificare reusita: True`, `Proiect conectat: your-gcp-project-id`)*.


---

## 🌐 Usage in VS Code Web (`code-server` on Port 9080)

If you are using VS Code running directly on the server via `code-server` (accessible from the browser at `http://<SERVER_IP>:9080` according to [vscode.md](vscode.md)):

### 1. Is a restart required after installing Cline in code-server?
* **Linux Server:** **NO**, the server does not need to be restarted.
* **Browser / VS Code:** Typically, the extension is active immediately. If the Cline icon does not appear in the left sidebar, a simple **page refresh** (`F5` or `Ctrl+R`) or `Ctrl+Shift+P` ➡️ **`Developer: Reload Window`** is sufficient.
* Only if the extension throws memory errors or has stuck processes:
  
```bash
  sudo systemctl restart code-server@root
  ```### 2. Connection Options in Cline on code-server:

#### Option A: Via Local LiteLLM (Recommended)
* Cline panel ➡️ **⚙️ Settings**
* **API Provider:** `OpenAI Compatible`
* **Base URL:** `http://localhost:4000/v1`
* **API Key:** `dummy`
* **Model ID:** `Gemini 3.8 Flash` or `Gemini 3.1 Pro Preview`

#### Option B: Directly via Google Cloud Vertex AI
* Cline panel ➡️ **⚙️ Settings**
* **API Provider:** `Google Vertex AI`
* **GCP Project ID:** `your-gcp-project-id`
* **GCP Region:** `us-central1`
* **Model:** `gemini-2.5-pro` (or `gemini-2.0-flash`)
* The SA key `/path/to/your/vertex-sa-credentials.json` is already present on the system and validated.