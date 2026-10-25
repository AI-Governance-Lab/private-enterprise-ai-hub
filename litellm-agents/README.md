# LiteLLM Agents Gateway (`litellm-agents` — Port 4001) 🤖💻

A dedicated, isolated **LiteLLM Proxy** instance built specifically for autonomous coding agents and IDE extensions:
- **Cline** (VS Code / `code-server`)
- **Roo Code** (VS Code / `code-server`)
- **Continue.dev / Aider / Cursor** or any OpenAI-compatible developer tool

---

## 🎯 Why a Separate LiteLLM Instance?

Previously, a single `litellm` container (Port `4000`) served both **Open WebUI** (`private-enterprise-ai-hub`) and **Cline / Roo Code**. That caused two issues:
1. **Redeploy Interruptions:** Running `./run.sh` (or modifying `litellm_config.yaml` for Open WebUI) killed and recreated `litellm`, interrupting active Cline/Roo Code coding sessions mid-task.
2. **Tool-Calling vs. Search Grounding:** Open WebUI benefits from `googleSearch: {}` grounding on Gemini models, whereas autonomous coding agents send their own function/tool schemas (`read_files`, `editor`, `execute_command`, etc.) which can conflict with Vertex AI search grounding.

### Architecture Isolation

| Gateway | Container Name | Host Port | Config File | Managed By | Purpose |
|---|---|---|---|---|---|
| **Main AI Hub Proxy** | `litellm` | `4000` | `litellm_config.yaml` | `./run.sh` | Open WebUI chat, RAG embeddings, web search grounding |
| **Coding Agents Proxy** | `litellm-agents` | **`4001`** | `litellm-agents/litellm_config.yaml` | `./litellm-agents/run.sh` | **Cline, Roo Code, IDE coding & architecture agents** |

---

## 🚀 Quick Start & Maintenance Commands

### 1. Start or Recreate `litellm-agents`
```bash
cd litellm-agents
./run.sh
```

### 2. Reload Configuration After Editing `litellm_config.yaml` (~3 seconds)
Because `litellm_config.yaml` is bind-mounted into the container, you can apply model changes without recreating the container:
```bash
docker restart litellm-agents
```

### 3. Check Health & Registered Models
```bash
# Liveliness check
curl -fsS http://127.0.0.1:4001/health/liveliness

# List available models
source .env
curl -s -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4001/v1/models | jq -r '.data[].id'
```

### 4. View Live Logs
```bash
docker logs -f litellm-agents
```

---

## ⚙️ Configuring Cline & Roo Code (Port `4001`)

Open **VS Code / `code-server`** (`http://localhost:9080`) and update the extension settings to point to port **`4001`**:

### Cline Setup
1. Open the **Cline** sidebar → click the ⚙️ (**Settings**) icon.
2. Configure:
   - **API Provider:** `OpenAI Compatible` (or `LiteLLM`)
   - **Base URL:** `http://localhost:4001/v1`
   - **API Key:** Your `LITELLM_MASTER_KEY` from `.env`
   - **Model ID:**
     - `glm-5.2` *(Zhipu GLM 5.2 on Vertex AI MaaS — 1M context, strong agentic coding & reasoning)*
     - `gemini-3.8-flash` *(fast daily agentic coding)*
     - `gemini-3.1-pro-preview` *(deep reasoning & complex architecture)*
     - `codestral-2508` *(specialized Mistral coding model, 256k context)*
     - `cohere/north-mini-code:free` *(free OpenRouter coding model with automatic fallback)*

### Roo Code Multi-Mode Setup
1. Open the **Roo Code** sidebar → click ⚙️ (**Settings**).
2. Set **Base URL** to `http://localhost:4001/v1` and **API Key** to `LITELLM_MASTER_KEY`.
3. Recommended models per mode:
   - **`Code` Mode:** `glm-5.2`, `codestral-2508`, `gemini-3.8-flash`, or `cohere/north-mini-code:free`
   - **`Architect` Mode:** `glm-5.2`, `gemini-3.1-pro-preview`, `nvidia/nemotron-3-ultra-550b-a55b`, or `dots-studio/dots-3-note-preview:free`
   - **`Ask` Mode:** `gemini-3.8-flash` or `inclusionai/ling-3.0-flash-vl:free`
   - **Codebase Indexing (Embeddings):** `text-embedding-004` or `codestral-embed` on `http://localhost:4001/v1`

---

## 🔐 Secrets, Ports & Home LAN Configuration (`.env`)

All ports, bind IPs, container names, and API keys are loaded from `.env` (which is excluded from Git via `.gitignore` and locked with `chmod 600` permissions):

```env
# Network & Container Configuration (Home LAN / Local Access)
LITELLM_AGENTS_CONTAINER=litellm-agents
LITELLM_AGENTS_BIND_IP=0.0.0.0
LITELLM_AGENTS_PORT=4001
DOCKER_NETWORK=private-ai-net
LITELLM_IMAGE=ghcr.io/berriai/litellm:main-latest

# Cloud Credentials & API Keys
GCP_CREDENTIALS_FILE=credentials.json
GCP_PROJECT_ID=your-gcp-project-id
LITELLM_MASTER_KEY=replace_with_a_secure_random_string
MISTRAL_API_KEY=your_mistral_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
NVIDIA_API_KEY=your_nvidia_api_key_here
```

- **Use across all computers at home:** Keep `LITELLM_AGENTS_BIND_IP=0.0.0.0` (or set it to your Linux server's static LAN IP) and connect from any PC/laptop on your home network using `http://<YOUR_SERVER_LAN_IP>:<LITELLM_AGENTS_PORT>/v1` with your `LITELLM_MASTER_KEY`.
- **Single-machine only mode:** Set `LITELLM_AGENTS_BIND_IP=127.0.0.1` in `.env` to restrict access strictly to `localhost`.
- **Safe to publish on GitHub:** Only `.env.example` is tracked by Git; your real `.env` and `credentials/*.json` are ignored by `.gitignore`.

---

## 🔄 Auto-Start at Boot on Linux (`systemd`)

To automatically start `litellm-agents` when your Linux server boots:

**1. Create `/etc/systemd/system/litellm-agents.service`:**
```ini
[Unit]
Description=LiteLLM Coding Agents Gateway (litellm-agents)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
WorkingDirectory=/opt/private-enterprise-ai-hub/litellm-agents
ExecStart=/opt/private-enterprise-ai-hub/litellm-agents/run.sh
ExecStop=/usr/bin/docker stop litellm-agents
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```
*(Update `WorkingDirectory` and `ExecStart` to match the path where you cloned the repository).*

**2. Enable and start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now litellm-agents.service
sudo systemctl status litellm-agents.service --no-pager
```

