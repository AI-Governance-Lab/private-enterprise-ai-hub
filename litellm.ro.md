[English](litellm.md) | [Română](litellm.ro.md) | [Français](litellm.fr.md)

---

# Ghid de Integrare și Arhitectură LiteLLM 🚀

Acest document oferă un ghid complet pentru **LiteLLM** în cadrul stack-ului Private Enterprise AI Hub, detaliind modelele disponibile, autentificarea și configurarea pas cu pas pentru **Cline**, **Roo Code** și **Open WebUI**.

---

## 🏗️ 1. Prezentare Generală a Arhitecturii


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


LiteLLM funcționează ca un **gateway și proxy LLM multi-provider** de înaltă performanță:
1. Traduce cererile din formatul standard OpenAI API în apeluri specifice fiecărui provider (Google Vertex AI, Mistral AI, OpenRouter, NVIDIA NIM).
2. Centralizează credențialele de autentificare (GCP Service Account JSON, Mistral API Key, OpenRouter API Key, NVIDIA API Key).
3. Oferă un singur endpoint (`http://localhost:4000/v1`) pentru Open WebUI, Cline, Roo Code, scripturi și servicii interne.

---

## 🤖 2. Catalog de Modele și Capabilități

### Modele Comerciale & Private Cloud
| Nume Afișat Model | ID Model Intern / Alias | Provider | Recomandat Pentru | Fereastră de Context |
|---|---|---|---|---|
| **Codestral (codestral-2508)** | `codestral-2508` | Mistral AI | **Coding, refactoring, bug fixing, Fill-in-the-Middle** | 256,000 tokens |
| **Gemini 3.1 Pro Preview** | `Gemini 3.1 Pro Preview` | Google Vertex AI | **Deep reasoning, arhitectură complexă, web search** | 1,048,576 tokens |
| **Gemini 3.8 Flash** | `Gemini 3.8 Flash` | Google Vertex AI | **Răspunsuri instantanee (1-3s), chat de zi cu zi, web search** | 1,048,576 tokens |
| **Argon (Gemini 4 Argon)** | `gemini-4-argon` | Google Vertex AI | **Model Gemini 4 Argon** | Nespecificat |
| **Ministral 14B** | `Ministral 14B`<br>`Mistral 14B`<br>`ministral-14b-latest`<br>`ministral-14b` | Mistral AI | **Cunoștințe generale, sarcini multilingve, instrucțiuni** | 262,144 tokens |
| **text-embedding-004** | `text-embedding-004` | Google Vertex AI | **Document RAG, căutare semantică în PDF-uri** (768 dimensiuni) | 2,048 tokens |
| **codestral-embed** | `codestral-embed` | Mistral AI | **Code RAG, căutare semantică în depozite de cod** (1536 dim) | 8,192 tokens |
| **mistral-embed** | `mistral-embed` | Mistral AI | **RAG pentru text în limbaj natural** (1024 dimensiuni) | 8,192 tokens |### Modele gratuite OpenRouter (Cost: $0.00)
| Nume afișat model | ID intern model / Alias | Furnizor | Rol & Capabilități | Fereastră de context |
|---|---|---|---|---|
| **OpenRouter North Code** | `cohere/north-mini-code:free` | OpenRouter (Cohere) | **💻 CODING:** Model agentic 30B MoE optimizat pentru scriere cod, debugging și refactoring cu raționament pas-cu-pas. | 256.000 tokens |
| **OpenRouter Nex Coding** | `nex-agi/nex-n2.5-pro:free` | OpenRouter (Nex AGI) | **💻 CODING (Agentic):** Specializat pe parcurgere repo-uri și modificări de cod multi-file cu buclă de verificare. | 262.144 tokens |
| **OpenRouter Ling Flash VL** | `inclusionai/ling-3.0-flash-vl:free` | OpenRouter (inclusionAI) | **🌐 GENERAL & MULTIMODAL:** Model 124B MoE foarte rapid (2-3s), suportă text + imagini/screenshot-uri, sarcini zilnice. | 262.144 tokens |
| **OpenRouter Auto Free** | `openrouter/free` | OpenRouter | **🌐 GENERAL (Fail-safe):** Router inteligent care comută automat pe cel mai bun model gratuit disponibil în acel moment. | 200.000 tokens |
| **OpenRouter Dots3 Architecture** | `dots-studio/dots-3-note-preview:free` | OpenRouter (Dots Studio) | **🏛️ ARHITECTURĂ:** Model masiv de 280B MoE (16B activi) cu gândire profundă pentru scheme tehnice și structură de sistem. | 512.000 tokens |
### Modele NVIDIA Developer NIM (integrate.api.nvidia.com)
| Nume afișat model | ID intern model / Alias | Furnizor | Rol & Capabilități |
|---|---|---|---|
| **NVIDIA GPT-OSS 20B** | `openai/gpt-oss-20b` | NVIDIA NIM (OpenAI) | **💻 CODING:** Model ultra-rapid (~0.5s) rulat pe clustere NVIDIA, ideal pentru cod curat, testat și refactoring. |
| **NVIDIA DeepSeek v4 Flash** | `deepseek-ai/deepseek-v4-flash-0731` | NVIDIA NIM (DeepSeek) | **💻 CODING:** Model de mare viteză cu raționament avansat pentru sarcini de codare complexe. |
| **NVIDIA Nemotron Ultra 550B** | `nvidia/nemotron-3-ultra-550b-a55b` | NVIDIA NIM | **🏛️ ARHITECTURĂ:** Model frontier MoE de 550B (55B activi), cu context de până la 1 milion de tokens, pentru raționament avansat și arhitectură de sistem. |
| **NVIDIA Nemotron Super 120B** | `nvidia/nemotron-3-super-120b-a12b` | NVIDIA NIM | **🏛️ ARHITECTURĂ:** Model masiv de 120B MoE (12B activi), hibrid Transformer-Mamba, ideal pentru system design. |
| **NVIDIA Nemotron Reasoning** | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | NVIDIA NIM | **🏛️ ARHITECTURĂ:** Model 30B MoE optimizat pentru raționament rapid, planificare arhitecturală și sub-agenți. |
| **NVIDIA Llama 3.2 11B Vision** | `meta/llama-3.2-11b-vision-instruct` | NVIDIA NIM (Meta) | **🌐 GENERAL & MULTIMODAL:** Modelul oficial Meta LLaMA 3.2 (text + imagini), fluent în română, foarte stabil. |
| **NVIDIA Nemotron Lightning 30B** | `nvidia/nemotron-3.5-lightning-30b-a3b` | NVIDIA NIM | **🌐 GENERAL:** Model MoE de 30B cu latență mică și randament ridicat pentru conversații zilnice. |

---

## 💻 3. Configurarea Roo Code în VS Code

Roo Code este conceput pentru programare autonomă și operațiuni multi-mode. Acesta se conectează la LiteLLM prin intermediul provider-ului standard OpenAI Compatible.### Pași de configurare:
1. Deschideți **VS Code / code-server** (`http://localhost:9080`).
2. Deschideți panoul **Roo Code** din bara laterală din stânga.
3. Faceți clic pe pictograma ⚙️ (**Settings**) din partea de sus a panoului Roo Code.
4. Setați următorii parametri:
   - **API Provider:** `OpenAI Compatible`
   - **Base URL:** `http://localhost:4000/v1`
   - **API Key:** `dummy` *(sau orice text substituent/placeholder, de ex. `sk-litellm`)*
   - **Model ID:** `codestral-2508` *(sau selectați `Codestral (codestral-2508)`)*
   - **Context Window:** `256000` *(corespunde limitei maxime de context a modelului Codestral)*
   - **Max Output Tokens:** `8192` (sau lăsați valoarea implicită)
5. Faceți clic pe **Save**.

### 🌟 Configurare Multi-Mode recomandată în Roo Code:
Roo Code permite alocarea unor modele diferite pentru moduri operaționale specifice:

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

## 🛠️ 4. Configurarea Cline în VS Code

Cline se conectează la LiteLLM prin exact aceeași interfață OpenAI-compatible:

1. Deschideți panoul **Cline** în VS Code.
2. Faceți clic pe pictograma ⚙️ (**Settings**).
3. Configurați câmpurile:
   - **API Provider:** `OpenAI Compatible`
   - **Base URL:** `http://localhost:4000/v1`
   - **API Key:** `dummy`
   - **Model ID:** `cohere/north-mini-code:free` *(pentru mod gratuit)* sau `codestral-2508`
4. Faceți clic pe **Save Settings**.

---

## 🌐 5. Integrarea cu Open WebUI

Open WebUI interoghează automat endpoint-ul `/models` al LiteLLM în interiorul rețelei private (`http://litellm:4000`).### Disponibilitatea modelelor:
Toate modelele înregistrate în `litellm_config.yaml` sunt disponibile imediat în Open WebUI:
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

### RAG și embedding-uri pentru documente:
În mod implicit, Open WebUI utilizează `text-embedding-004` prin LiteLLM pentru embedding și regăsirea documentelor (retrieval). De asemenea, puteți configura bazele de cunoștințe (knowledge bases) să utilizeze `codestral-embed` sau `mistral-embed` navigând la:
`Admin Panel -> Settings -> Retrieval -> Embedding Model Engine: OpenAI -> Embedding Model: codestral-embed`.

---

## 🔐 6. Configurare și gestionarea secretelor

Configurația este gestionată prin intermediul a trei fișiere:

### 1. `.env` (Variabile de mediu și chei API)

```bash
GCP_CREDENTIALS_FILE=${GCP_CREDENTIALS_FILE:-credentials.json}
GCP_PROJECT_ID=${GCP_PROJECT_ID:-your-gcp-project-id}
WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY:-your-secret-key}
MISTRAL_API_KEY=${MISTRAL_API_KEY:-your-mistral-api-key}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-your-openrouter-api-key}
NVIDIA_API_KEY=${NVIDIA_API_KEY:-your-nvidia-api-key}
```


### 2. `run.sh` (Orchestrarea containerelor)
`run.sh` transmite cheile către containerul `litellm`:

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


### 3. `litellm_config.yaml` (Declararea modelelor)
Declară maparea dintre denumirile afișate utilizatorilor (user-facing) și modelele furnizorilor upstream:

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

## 🔍 7. Comenzi de verificare și Health Check

Rulați aceste comenzi din terminalul host pentru a verifica dacă LiteLLM funcționează corect:

### Listarea modelelor disponibile:

```bash
curl -s http://localhost:4000/v1/models | jq '.data[].id'
```


### Testare chat completion Codestral:

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


### Testare model OpenRouter Free Coding (Cohere North Mini Code):

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


### Testare model OpenRouter Free General (Ling Flash VL):

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


### Testare model NVIDIA Developer NIM Coding (GPT-OSS 20B):

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


### Testare model NVIDIA Developer NIM General Multimodal (LLaMA 3.2 11B Vision):

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


### Testare generare embeddings:

```bash
curl -s http://localhost:4000/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "codestral-embed",
    "input": "function test() {}"
  }' | jq '.data[0].embedding | length'
```

*(Ar trebui să returneze `1536`)*

### Vizualizare loguri LiteLLM în timp real:

```bash
docker logs -f litellm
```