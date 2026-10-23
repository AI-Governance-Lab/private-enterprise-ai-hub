[English](litellm.md) | [Română](litellm.ro.md) | [Français](litellm.fr.md)

---


# LiteLLM Integration & Architecture Guide 🚀

This document provides a comprehensive guide to **LiteLLM** within the Private Enterprise AI Hub stack, detailing available models, authentication, and step-by-step setup for **Cline**, **Roo Code**, and **Open WebUI**.

---

## 🏗️ 1. Architecture Overview

```
                          ┌──────────────────────────────────────────────┐
                          │         Client Applications                  │
                          │                                              │
                          │  • Open WebUI (Browser UI - Port 8080)       │
                          │  • Roo Code Extension (VS Code - Port 9080)   │
                          │  • Cline Extension (VS Code - Port 9080)      │
                          └──────────────────────┬───────────────────────┘
                                                 │
                                                 │ OpenAI API Compatible
                                                 │ http://localhost:4000/v1
                                                 │ (or http://litellm:4000/v1)
                                                 ▼
                          ┌──────────────────────────────────────────────┐
                          │       LiteLLM Proxy (Port 4000)              │
                          │       Container: `litellm`                   │
                          │       Config: `litellm_config.yaml`          │
                          └──────┬───────────┬───────────┬───────────┬───┘
                                 │           │           │           │
            Google Vertex AI API │Mistral API│OpenRouter │NVIDIA NIM │
       (GCP Service Account Auth)│(MISTRAL)  │(OPENROUTER│(NVIDIA_KEY│
                                 ▼           ▼           ▼           ▼
                  ┌──────────────┐ ┌────────┐ ┌──────────┐ ┌─────────────────────────┐
                  │Vertex AI     │ │Mistral │ │OpenRouter│ │NVIDIA Developer NIM     │
                  │•Gemini3.1 Pro│ │•Codestr│ │•NorthCode│ │•GPT-OSS 20B (Coding)    │
                  │•Gemini Flash │ │•Ministr│ │•LingFlash│ │•DeepSeek v4 Flash (Code)│
                  │•text-embed   │ │•embeds │ │•Dots3 MoE│ │•Nemotron Super 120B(Arh)│
                  │              │ │        │ │•FreeRoute│ │•Nemotron Reasoning 30B │
                  │              │ │        │ │          │ │•Llama 3.2 11B Vision    │
                  └──────────────┘ └────────┘ └──────────┘ └─────────────────────────┘
```

LiteLLM acts as a high-performance **multi-provider LLM gateway and proxy**:
1. Translates requests from standard OpenAI API format into provider-specific calls (Google Vertex AI, Mistral AI, OpenRouter, NVIDIA NIM).
2. Centralizes authentication credentials (GCP Service Account JSON, Mistral API Key, OpenRouter API Key, NVIDIA API Key).
3. Provides a single endpoint (`http://localhost:4000/v1`) for Open WebUI, Cline, Roo Code, scripts, and internal services.

---

## 🤖 2. Model Catalog & Capabilities

### Commercial & Private Cloud Models
| Model Display Name | Internal Model ID / Alias | Provider | Best Used For | Context Window |
|---|---|---|---|---|
| **Codestral (codestral-2508)** | `codestral-2508` | Mistral AI | **Coding, refactoring, bug fixing, Fill-in-the-Middle** | 256,000 tokens |
| **Gemini 3.1 Pro Preview** | `Gemini 3.1 Pro Preview` | Google Vertex AI | **Deep reasoning, complex architecture, web search** | 1,048,576 tokens |
| **Gemini 3.8 Flash** | `Gemini 3.8 Flash` | Google Vertex AI | **Instant responses (1-3s), everyday chat, web search** | 1,048,576 tokens |
| **Argon (Gemini 4 Argon)** | `gemini-4-argon` | Google Vertex AI | **Gemini 4 Argon** | Not specified |
| **GLM 5.2 (GLM-5.2)** | `glm-5.2`<br>`glm-5.2-maas`<br>`GLM 5.2` | Google Vertex AI (Zhipu MaaS) | **1M context, advanced coding with flexible thinking effort, long-horizon agentic tasks** | 1,000,000 tokens |
| **Ministral 14B** | `Ministral 14B`<br>`Mistral 14B`<br>`ministral-14b-latest`<br>`ministral-14b` | Mistral AI | **General knowledge, multilingual tasks, instructions** | 262,144 tokens |
| **text-embedding-004** | `text-embedding-004` | Google Vertex AI | **Document RAG, PDF semantic search** (768 dimensions) | 2,048 tokens |
| **codestral-embed** | `codestral-embed` | Mistral AI | **Code RAG, code repository semantic search** (1536 dim) | 8,192 tokens |
| **mistral-embed** | `mistral-embed` | Mistral AI | **Natural language text RAG** (1024 dimensions) | 8,192 tokens |

### OpenRouter Free Models (Cost: $0.00)
| Model Display Name | Internal Model ID / Alias | Provider | Role & Capabilities | Context Window |
|---|---|---|---|---|
| **OpenRouter North Code** | `cohere/north-mini-code:free` | OpenRouter (Cohere) | **💻 CODING:** Model agentic 30B MoE optimizat pentru scriere cod, debugging și refactoring cu raționament pas-cu-pas. | 256,000 tokens |
| **OpenRouter Nex Coding** | `nex-agi/nex-n2.5-pro:free` | OpenRouter (Nex AGI) | **💻 CODING (Agentic):** Specializat pe parcurgere repo-uri și modificări de cod multi-file cu buclă de verificare. | 262,144 tokens |
| **OpenRouter Ling Flash VL** | `inclusionai/ling-3.0-flash-vl:free` | OpenRouter (inclusionAI) | **🌐 GENERAL & MULTIMODAL:** Model 124B MoE foarte rapid (2-3s), suportă text + imagini/screenshot-uri, sarcini zilnice. | 262,144 tokens |
| **OpenRouter Auto Free** | `openrouter/free` | OpenRouter | **🌐 GENERAL (Fail-safe):** Router inteligent care comută automat pe cel mai bun model gratuit disponibil în acel moment. | 200,000 tokens |
| **OpenRouter Dots3 Architecture** | `dots-studio/dots-3-note-preview:free` | OpenRouter (Dots Studio) | **🏛️ ARHITECTURĂ:** Model masiv de 280B MoE (16B activi) cu gândire profundă pentru scheme tehnice și structură de sistem. | 512,000 tokens |
### NVIDIA Developer NIM Models (integrate.api.nvidia.com)
| Model Display Name | Internal Model ID / Alias | Provider | Role & Capabilities |
|---|---|---|---|
| **NVIDIA GPT-OSS 20B** | `openai/gpt-oss-20b` | NVIDIA NIM (OpenAI) | **💻 CODING:** Model ultra-rapid (~0.5s) rulat pe clustere NVIDIA, ideal pentru cod curat, testat și refactoring. |
| **NVIDIA DeepSeek v4 Flash** | `deepseek-ai/deepseek-v4-flash-0731` | NVIDIA NIM (DeepSeek) | **💻 CODING:** Model de mare viteză cu raționament avansat pentru sarcini de codare complexe. |
| **NVIDIA Nemotron Ultra 550B** | `nvidia/nemotron-3-ultra-550b-a55b` | NVIDIA NIM | **🏛️ ARCHITECTURE:** Frontier 550B MoE model (55B active) with up to 1 million tokens of context for advanced reasoning and system architecture. |
| **NVIDIA Nemotron Super 120B** | `nvidia/nemotron-3-super-120b-a12b` | NVIDIA NIM | **🏛️ ARHITECTURĂ:** Model masiv de 120B MoE (12B activi), hibrid Transformer-Mamba, ideal pentru system design. |
| **NVIDIA Nemotron Reasoning** | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | NVIDIA NIM | **🏛️ ARHITECTURĂ:** Model 30B MoE optimizat pentru raționament rapid, planificare arhitecturală și sub-agenți. |
| **NVIDIA Llama 3.2 11B Vision** | `meta/llama-3.2-11b-vision-instruct` | NVIDIA NIM (Meta) | **🌐 GENERAL & MULTIMODAL:** Modelul oficial Meta LLaMA 3.2 (text + imagini), fluent în română, foarte stabil. |
| **NVIDIA Nemotron Lightning 30B** | `nvidia/nemotron-3.5-lightning-30b-a3b` | NVIDIA NIM | **🌐 GENERAL:** Model MoE de 30B cu latență mică și randament ridicat pentru conversații zilnice. |

---

## 💻 3. Setting Up Roo Code in VS Code

Roo Code is designed for autonomous coding and multi-mode operations. It connects to LiteLLM via the standard OpenAI Compatible provider.

### Configuration Steps:
1. Open **VS Code / code-server** (`http://localhost:9080`).
2. Open the **Roo Code** panel on the left sidebar.
3. Click the ⚙️ (**Settings**) icon at the top of the Roo Code panel.
4. Set the following parameters:
   - **API Provider:** `OpenAI Compatible`
   - **Base URL:** `http://localhost:4000/v1`
  - **API Key:** The value of `LITELLM_MASTER_KEY` in the server's `.env` file
  - **Model ID:** `codestral-2508` *(or another exact ID returned by `/v1/models`)*
   - **Context Window:** `256000` *(matches Codestral's full context limit)*
   - **Max Output Tokens:** `8192` (or leave default)
5. Click **Save**.

The `Base URL` must resolve from the machine running Cline. For Cline in code-server on the same host as LiteLLM, `localhost` works. For desktop VS Code on another machine, replace `localhost` with the server's reachable hostname or IP. LiteLLM's `/v1` root may return HTTP 404; Cline uses endpoints such as `/v1/models` and `/v1/chat/completions`.

### 🌟 Recommended Multi-Mode Setup in Roo Code:
Roo Code allows assigning different models to specific operational modes:

#### Opțiunea 1: Stack Free (100% Gratuit prin OpenRouter)
* **`Code` Mode (Scriere și modificare cod):**
  - **Model ID:** `cohere/north-mini-code:free` (sau `nex-agi/nex-n2.5-pro:free`)
  - *Avantaj:* Model MoE specializat pe programare agentică, înțelege română, produce cod curat și validat.
* **`Architect` Mode (Design de sistem, analiză structurală, diagrame):**
  - **Model ID:** `dots-studio/dots-3-note-preview:free` (sau `nvidia/nemotron-3-ultra-550b-a55b`)
  - *Avantaj:* 512k - 1M tokens context, capacitate profundă de raționament arhitectural.
* **`Ask` Mode (Conversații zilnice, explicații, sinteze):**
  - **Model ID:** `inclusionai/ling-3.0-flash-vl:free` (sau `openrouter/free`)
  - *Avantaj:* Foarte rapid (2-3s), multimodal (înțelege și imagini/screenshot-uri).

#### Opțiunea 2: Stack Hybrid (Mistral AI + Google Vertex AI + OpenRouter + NVIDIA)
* **`Code` Mode:** `openai/gpt-oss-20b` sau `codestral-2508`
* **`Architect` Mode:** `Gemini 3.1 Pro Preview` sau `nvidia/nemotron-3-super-120b-a12b`
* **`Ask` Mode:** `meta/llama-3.2-11b-vision-instruct` sau `Gemini 3.8 Flash`

#### Opțiunea 3: Stack NVIDIA NIM (Developer Cloud)
* **`Code` Mode:** `openai/gpt-oss-20b` (sau `deepseek-ai/deepseek-v4-flash-0731`)
* **`Architect` Mode:** `nvidia/nemotron-3-ultra-550b-a55b` (sau `nvidia/nemotron-3-super-120b-a12b`)
* **`Ask` Mode:** `meta/llama-3.2-11b-vision-instruct` (sau `nvidia/nemotron-3.5-lightning-30b-a3b`)

---

## 🛠️ 4. Setting Up Cline in VS Code

Cline connects to LiteLLM through the exact same OpenAI-compatible interface:

1. Open the **Cline** panel in VS Code.
2. Click the ⚙️ (**Settings**) icon.
3. Configure the fields:
   - **API Provider:** `OpenAI Compatible`
   - **Base URL:** `http://localhost:4000/v1`
  - **API Key:** The value of `LITELLM_MASTER_KEY` in the server's `.env` file
   - **Model ID:** `cohere/north-mini-code:free` *(pentru mod gratuit)* sau `codestral-2508`
4. Click **Save Settings**.

---

## 🌐 5. Integration with Open WebUI

Open WebUI automatically queries LiteLLM's `/models` endpoint inside the private network (`http://litellm:4000`).

### Model Availability:
All models registered in `litellm_config.yaml` are immediately available in Open WebUI:
- `Codestral (codestral-2508)`
- `Ministral 14B`
- `Gemini 3.1 Pro Preview`
- `Gemini 3.8 Flash`
- `OpenRouter North Code (cohere-north-mini-code:free)`
- `OpenRouter Nex Coding (nex-n2.5-pro:free)`
- `OpenRouter Ling Flash VL (ling-3.0-flash-vl:free)`
- `OpenRouter Auto Free (openrouter/free)`
- `OpenRouter Dots3 Architecture (dots-3-note-preview:free)`
- `NVIDIA GPT-OSS 20B (openai/gpt-oss-20b)`
- `NVIDIA DeepSeek v4 Flash (deepseek-v4-flash-0731)`
- `NVIDIA Nemotron Ultra 550B (nemotron-3-ultra-550b-a55b)`
- `NVIDIA Nemotron Super 120B (nemotron-3-super-120b-a12b)`
- `NVIDIA Nemotron Reasoning (nemotron-3-nano-omni-30b)`
- `NVIDIA Llama 3.2 11B Vision (llama-3.2-11b-vision-instruct)`
- `NVIDIA Nemotron Lightning 30B (nemotron-3.5-lightning-30b)`

### RAG & Document Embeddings:
By default, Open WebUI uses `text-embedding-004` through LiteLLM for document embedding and retrieval. You can also configure knowledge bases to use `codestral-embed` or `mistral-embed` via:
`Admin Panel -> Settings -> Retrieval -> Embedding Model Engine: OpenAI -> Embedding Model: codestral-embed`.

---

## 🔐 6. Configuration & Secrets Management

The configuration is managed across three files:

### 1. `.env` (Environment variables and API keys)
```bash
GCP_CREDENTIALS_FILE=${GCP_CREDENTIALS_FILE:-credentials.json}
GCP_PROJECT_ID=${GCP_PROJECT_ID:-your-gcp-project-id}
WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY:-your-secret-key}
MISTRAL_API_KEY=${MISTRAL_API_KEY:-your-mistral-api-key}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-your-openrouter-api-key}
NVIDIA_API_KEY=${NVIDIA_API_KEY:-your-nvidia-api-key}
```

### 2. `run.sh` (Container orchestration)
`run.sh` forwards the keys into the `litellm` container:
```bash
docker run -d \
    --name litellm \
    --network private-ai-net \
    --restart unless-stopped \
    -p 4000:4000 \
    -v $(pwd)/litellm_config.yaml:/app/config.yaml:ro \
    -v $(pwd)/"${GCP_CREDENTIALS_FILE:-credentials.json}":/app/credentials.json:ro \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
    -e GCP_PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}" \
    -e MISTRAL_API_KEY="${MISTRAL_API_KEY:-your-mistral-api-key}" \
    -e OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-your-openrouter-api-key}" \
    -e NVIDIA_API_KEY="${NVIDIA_API_KEY:-your-nvidia-api-key}" \
    "$LITELLM_IMAGE" \
    --config /app/config.yaml --detailed_debug
```

### 3. `litellm_config.yaml` (Model declarations)
Declares the mapping between user-facing names and upstream provider models:
```yaml
model_list:
  # Google Vertex AI Models
  - model_name: Gemini 3.1 Pro Preview
    litellm_params:
      model: vertex_ai/gemini-3.1-pro-preview
      vertex_project: "os.environ/GCP_PROJECT_ID"
      vertex_location: "global"
      tools:
        - googleSearch: {}

  - model_name: Gemini 3.8 Flash
    litellm_params:
      model: vertex_ai/gemini-3.8-flash
      vertex_project: "os.environ/GCP_PROJECT_ID"
      vertex_location: "global"
      tools:
        - googleSearch: {}

  - model_name: text-embedding-004
    litellm_params:
      model: vertex_ai/text-embedding-004
      vertex_project: "os.environ/GCP_PROJECT_ID"
      vertex_location: "global"

  # Mistral AI Models
  - model_name: Codestral (codestral-2508)
    litellm_params:
      model: mistral/codestral-2508
      api_key: "os.environ/MISTRAL_API_KEY"

  - model_name: codestral-2508
    litellm_params:
      model: mistral/codestral-2508
      api_key: "os.environ/MISTRAL_API_KEY"

  - model_name: Ministral 14B
    litellm_params:
      model: mistral/ministral-14b-latest
      api_key: "os.environ/MISTRAL_API_KEY"

  - model_name: codestral-embed
    litellm_params:
      model: mistral/codestral-embed
      api_key: "os.environ/MISTRAL_API_KEY"

  - model_name: mistral-embed
    litellm_params:
      model: mistral/mistral-embed
      api_key: "os.environ/MISTRAL_API_KEY"

  # OpenRouter Free Models
  - model_name: OpenRouter North Code (cohere-north-mini-code:free)
    litellm_params:
      model: openrouter/cohere/north-mini-code:free
      api_key: "os.environ/OPENROUTER_API_KEY"

  - model_name: cohere/north-mini-code:free
    litellm_params:
      model: openrouter/cohere/north-mini-code:free
      api_key: "os.environ/OPENROUTER_API_KEY"

  - model_name: inclusionai/ling-3.0-flash-vl:free
    litellm_params:
      model: openrouter/inclusionai/ling-3.0-flash-vl:free
      api_key: "os.environ/OPENROUTER_API_KEY"

  - model_name: dots-studio/dots-3-note-preview:free
    litellm_params:
      model: openrouter/dots-studio/dots-3-note-preview:free
      api_key: "os.environ/OPENROUTER_API_KEY"
```

---

## 🔍 7. Verification & Health Check Commands

Run these commands from the host terminal to verify that LiteLLM is functioning properly:

### List available models:
```bash
curl -s http://localhost:4000/v1/models | jq '.data[].id'
```

### Test Codestral chat completion:
```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "codestral-2508",
    "messages": [{"role": "user", "content": "Write a python hello world function"}],
    "max_tokens": 50
  }' | jq '.choices[0].message.content'
```

### Test OpenRouter Free Coding model (Cohere North Mini Code):
```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "cohere/north-mini-code:free",
    "messages": [{"role": "user", "content": "Write a python function to add two numbers"}],
    "max_tokens": 150
  }' | jq '.choices[0].message.content'
```

### Test OpenRouter Free General model (Ling Flash VL):
```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "inclusionai/ling-3.0-flash-vl:free",
    "messages": [{"role": "user", "content": "Salut, functionezi corect?"}],
    "max_tokens": 50
  }' | jq '.choices[0].message.content'
```

### Test NVIDIA Developer NIM Coding model (GPT-OSS 20B):
```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "messages": [{"role": "user", "content": "Write a python function to check prime numbers"}],
    "max_tokens": 150
  }' | jq '.choices[0].message.content'
```

### Test NVIDIA Developer NIM General Multimodal model (LLaMA 3.2 11B Vision):
```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "meta/llama-3.2-11b-vision-instruct",
    "messages": [{"role": "user", "content": "Salut! Raspunde scurt in limba romana."}],
    "max_tokens": 100
  }' | jq '.choices[0].message.content'
```

### Test Embedding generation:
```bash
curl -s http://localhost:4000/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "codestral-embed",
    "input": "function test() {}"
  }' | jq '.data[0].embedding | length'
```
*(Should return `1536`)*

### View live LiteLLM logs:
```bash
docker logs -f litellm
```
