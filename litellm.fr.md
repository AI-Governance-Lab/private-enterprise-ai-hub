[English](litellm.md) | [Română](litellm.ro.md) | [Français](litellm.fr.md)

---

# Guide d'intégration et d'architecture LiteLLM 🚀

Ce document fournit un guide complet sur **LiteLLM** au sein de la stack Private Enterprise AI Hub, détaillant les modèles disponibles, l'authentification et la configuration pas à pas pour **Cline**, **Roo Code** et **Open WebUI**.

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


LiteLLM agit comme une **passerelle et un proxy LLM multi-fournisseurs** haute performance :
1. Traduit les requêtes du format standard OpenAI API vers les appels spécifiques à chaque fournisseur (Google Vertex AI, Mistral AI, OpenRouter, NVIDIA NIM).
2. Centralise les identifiants d'authentification (GCP Service Account JSON, Mistral API Key, OpenRouter API Key, NVIDIA API Key).
3. Fournit un endpoint unique (`http://localhost:4000/v1`) pour Open WebUI, Cline, Roo Code, les scripts et les services internes.

---

## 🤖 2. Model Catalog & Capabilities

### Modèles commerciaux et Private Cloud
| Nom d'affichage du modèle | ID interne du modèle / Alias | Fournisseur | Idéal pour | Fenêtre de contexte |
|---|---|---|---|---|
| **Codestral (codestral-2508)** | `codestral-2508` | Mistral AI | **Coding, refactoring, bug fixing, Fill-in-the-Middle** | 256,000 tokens |
| **Gemini 3.1 Pro Preview** | `Gemini 3.1 Pro Preview` | Google Vertex AI | **Raisonnement approfondi, architecture complexe, recherche web** | 1,048,576 tokens |
| **Gemini 3.8 Flash** | `Gemini 3.8 Flash` | Google Vertex AI | **Réponses instantanées (1-3s), chat au quotidien, recherche web** | 1,048,576 tokens |
| **Argon (Gemini 4 Argon)** | `gemini-4-argon` | Google Vertex AI | **Modèle Gemini 4 Argon** | Non spécifiée |
| **Ministral 14B** | `Ministral 14B`<br>`Mistral 14B`<br>`ministral-14b-latest`<br>`ministral-14b` | Mistral AI | **Connaissances générales, tâches multilingues, instructions** | 262,144 tokens |
| **text-embedding-004** | `text-embedding-004` | Google Vertex AI | **RAG documentaire, recherche sémantique de PDF** (768 dimensions) | 2,048 tokens |
| **codestral-embed** | `codestral-embed` | Mistral AI | **RAG de code, recherche sémantique de dépôts de code** (1536 dim) | 8,192 tokens |
| **mistral-embed** | `mistral-embed` | Mistral AI | **RAG de texte en langage naturel** (1024 dimensions) | 8,192 tokens |### Modèles gratuits OpenRouter (Coût : $0.00)
| Nom d'affichage du modèle | ID interne du modèle / Alias | Fournisseur | Rôle et capacités | Fenêtre de contexte |
|---|---|---|---|---|
| **OpenRouter North Code** | `cohere/north-mini-code:free` | OpenRouter (Cohere) | **💻 CODING :** Modèle agentique MoE 30B optimisé pour l'écriture de code, le debugging et le refactoring avec raisonnement pas-à-pas. | 256,000 tokens |
| **OpenRouter Nex Coding** | `nex-agi/nex-n2.5-pro:free` | OpenRouter (Nex AGI) | **💻 CODING (Agentic) :** Spécialisé dans le parcours de dépôts et les modifications de code multi-fichiers avec boucle de vérification. | 262,144 tokens |
| **OpenRouter Ling Flash VL** | `inclusionai/ling-3.0-flash-vl:free` | OpenRouter (inclusionAI) | **🌐 GENERAL & MULTIMODAL :** Modèle MoE 124B très rapide (2-3s), prend en charge le texte + les images/captures d'écran, tâches quotidiennes. | 262,144 tokens |
| **OpenRouter Auto Free** | `openrouter/free` | OpenRouter | **🌐 GENERAL (Fail-safe) :** Routeur intelligent qui bascule automatiquement vers le meilleur modèle gratuit disponible à cet instant. | 200,000 tokens |
| **OpenRouter Dots3 Architecture** | `dots-studio/dots-3-note-preview:free` | OpenRouter (Dots Studio) | **🏛️ ARCHITECTURE :** Modèle massif MoE de 280B (16B actifs) avec réflexion approfondie pour les schémas techniques et la structure système. | 512,000 tokens |
### Modèles NVIDIA Developer NIM (integrate.api.nvidia.com)
| Nom d'affichage du modèle | ID interne du modèle / Alias | Fournisseur | Rôle et capacités |
|---|---|---|---|
| **NVIDIA GPT-OSS 20B** | `openai/gpt-oss-20b` | NVIDIA NIM (OpenAI) | **💻 CODING :** Modèle ultra-rapide (~0.5s) exécuté sur les clusters NVIDIA, idéal pour du code propre, testé et le refactoring. |
| **NVIDIA DeepSeek v4 Flash** | `deepseek-ai/deepseek-v4-flash-0731` | NVIDIA NIM (DeepSeek) | **💻 CODING :** Modèle haute vitesse avec raisonnement avancé pour les tâches complexes de codage. |
| **NVIDIA Nemotron Ultra 550B** | `nvidia/nemotron-3-ultra-550b-a55b` | NVIDIA NIM | **🏛️ ARCHITECTURE :** Modèle frontier MoE de 550B (55B actifs), avec un contexte allant jusqu'à 1 million de tokens, pour le raisonnement avancé et l'architecture système. |
| **NVIDIA Nemotron Super 120B** | `nvidia/nemotron-3-super-120b-a12b` | NVIDIA NIM | **🏛️ ARCHITECTURE :** Modèle massif MoE de 120B (12B actifs), hybride Transformer-Mamba, idéal pour le system design. |
| **NVIDIA Nemotron Reasoning** | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | NVIDIA NIM | **🏛️ ARCHITECTURE :** Modèle MoE 30B optimisé pour le raisonnement rapide, la planification architecturale et les sous-agents. |
| **NVIDIA Llama 3.2 11B Vision** | `meta/llama-3.2-11b-vision-instruct` | NVIDIA NIM (Meta) | **🌐 GENERAL & MULTIMODAL :** Le modèle officiel Meta LLaMA 3.2 (texte + images), fluide en roumain, très stable. |
| **NVIDIA Nemotron Lightning 30B** | `nvidia/nemotron-3.5-lightning-30b-a3b` | NVIDIA NIM | **🌐 GENERAL :** Modèle MoE de 30B à faible latence et haut débit pour les conversations quotidiennes. |

---

## 💻 3. Configuration de Roo Code dans VS Code

Roo Code est conçu pour le codage autonome et les opérations multi-modes. Il se connecte à LiteLLM via le fournisseur standard compatible OpenAI.### Étapes de configuration :
1. Ouvrez **VS Code / code-server** (`http://localhost:9080`).
2. Ouvrez le panneau **Roo Code** dans la barre latérale gauche.
3. Cliquez sur l'icône ⚙️ (**Settings**) en haut du panneau Roo Code.
4. Définissez les paramètres suivants :
   - **API Provider :** `OpenAI Compatible`
   - **Base URL :** `http://localhost:4000/v1`
   - **API Key :** `dummy` *(ou tout texte de remplacement, ex. `sk-litellm`)*
   - **Model ID :** `codestral-2508` *(ou sélectionnez `Codestral (codestral-2508)`)*
   - **Context Window :** `256000` *(correspond à la limite de contexte maximale de Codestral)*
   - **Max Output Tokens :** `8192` (ou laissez la valeur par défaut)
5. Cliquez sur **Save**.

### 🌟 Configuration multi-mode recommandée dans Roo Code :
Roo Code permet d'assigner différents modèles à des modes opérationnels spécifiques :

#### Option 1 : Stack Free (100 % gratuit via OpenRouter)
* **Mode `Code` (écriture et modification de code) :**
  - **Model ID :** `cohere/north-mini-code:free` (ou `nex-agi/nex-n2.5-pro:free`)
  - *Avantage :* Modèle MoE spécialisé dans la programmation agentique, comprend le roumain, produit un code propre et validé.
* **Mode `Architect` (conception système, analyse structurelle, diagrammes) :**
  - **Model ID :** `dots-studio/dots-3-note-preview:free` (ou `nvidia/nemotron-3-ultra-550b-a55b`)
  - *Avantage :* Contexte de 512k à 1M tokens, profonde capacité de raisonnement architectural.
* **Mode `Ask` (conversations quotidiennes, explications, synthèses) :**
  - **Model ID :** `inclusionai/ling-3.0-flash-vl:free` (ou `openrouter/free`)
  - *Avantage :* Très rapide (2-3s), multimodal (comprend également les images/captures d'écran).

#### Option 2 : Stack Hybrid (Mistral AI + Google Vertex AI + OpenRouter + NVIDIA)
* **Mode `Code` :** `openai/gpt-oss-20b` ou `codestral-2508`
* **Mode `Architect` :** `Gemini 3.1 Pro Preview` ou `nvidia/nemotron-3-super-120b-a12b`
* **Mode `Ask` :** `meta/llama-3.2-11b-vision-instruct` ou `Gemini 3.8 Flash`

#### Option 3 : Stack NVIDIA NIM (Developer Cloud)
* **Mode `Code` :** `openai/gpt-oss-20b` (ou `deepseek-ai/deepseek-v4-flash-0731`)
* **Mode `Architect` :** `nvidia/nemotron-3-ultra-550b-a55b` (ou `nvidia/nemotron-3-super-120b-a12b`)
* **Mode `Ask` :** `meta/llama-3.2-11b-vision-instruct` (ou `nvidia/nemotron-3.5-lightning-30b-a3b`)

---

## 🛠️ 4. Configuration de Cline dans VS Code

Cline se connecte à LiteLLM via exactement la même interface compatible OpenAI :

1. Ouvrez le panneau **Cline** dans VS Code.
2. Cliquez sur l'icône ⚙️ (**Settings**).
3. Configurez les champs :
   - **API Provider :** `OpenAI Compatible`
   - **Base URL :** `http://localhost:4000/v1`
   - **API Key :** `dummy`
   - **Model ID :** `cohere/north-mini-code:free` *(pour le mode gratuit)* ou `codestral-2508`
4. Cliquez sur **Save Settings**.

---

## 🌐 5. Intégration avec Open WebUI

Open WebUI interroge automatiquement l'endpoint `/models` de LiteLLM au sein du réseau privé (`http://litellm:4000`).### Disponibilité des modèles :
Tous les modèles enregistrés dans `litellm_config.yaml` sont immédiatement disponibles dans Open WebUI :
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

### RAG et embeddings de documents :
Par défaut, Open WebUI utilise `text-embedding-004` via LiteLLM pour l'embedding et la récupération de documents. Vous pouvez également configurer les bases de connaissances pour utiliser `codestral-embed` ou `mistral-embed` via :
`Admin Panel -> Settings -> Retrieval -> Embedding Model Engine: OpenAI -> Embedding Model: codestral-embed`.

---

## 🔐 6. Configuration et gestion des secrets

La configuration est gérée à travers trois fichiers :

### 1. `.env` (Variables d'environnement et clés API)

```bash
GCP_CREDENTIALS_FILE=${GCP_CREDENTIALS_FILE:-credentials.json}
GCP_PROJECT_ID=${GCP_PROJECT_ID:-your-gcp-project-id}
WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY:-your-secret-key}
MISTRAL_API_KEY=${MISTRAL_API_KEY:-your-mistral-api-key}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-your-openrouter-api-key}
NVIDIA_API_KEY=${NVIDIA_API_KEY:-your-nvidia-api-key}
```


### 2. `run.sh` (Orchestration des conteneurs)
`run.sh` transmet les clés au conteneur `litellm` :

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


### 3. `litellm_config.yaml` (Déclarations des modèles)
Déclare le mapping entre les noms destinés aux utilisateurs et les modèles des fournisseurs en amont :

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

## 🔍 7. Commandes de vérification et de health check

Exécutez ces commandes depuis le terminal de l'hôte pour vérifier que LiteLLM fonctionne correctement :

### Lister les modèles disponibles :

```bash
curl -s http://localhost:4000/v1/models | jq '.data[].id'
```


### Tester la complétion de chat Codestral :

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


### Tester le modèle de code gratuit OpenRouter (Cohere North Mini Code) :

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


### Tester le modèle généraliste gratuit OpenRouter (Ling Flash VL) :

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


### Tester le modèle de code NVIDIA Developer NIM (GPT-OSS 20B) :

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


### Tester le modèle multimodal généraliste NVIDIA Developer NIM (LLaMA 3.2 11B Vision) :

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


### Tester la génération d'embeddings :

```bash
curl -s http://localhost:4000/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "codestral-embed",
    "input": "function test() {}"
  }' | jq '.data[0].embedding | length'
```

*(Devrait retourner `1536`)*

### Consulter les logs LiteLLM en direct :

```bash
docker logs -f litellm
```