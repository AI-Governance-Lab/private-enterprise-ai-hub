# Zhipu GLM-5.2 on Google Cloud Vertex AI (MaaS) via LiteLLM Gateway

This guide explains how to integrate **GLM-5.2 (`zai-org/glm-5.2-maas`)** hosted on **Google Cloud Vertex AI Model-as-a-Service (MaaS)** with **LiteLLM (`litellm-agents` on Port `4001`)** for autonomous coding agents such as **Cline** and **Roo Code**.

---

## 1. Architectural Advantage of the LiteLLM Proxy Pattern

Google Cloud OAuth access tokens (`gcloud auth print-access-token`) expire every 60 minutes. Pasting raw OAuth tokens directly into IDE extensions causes session failures every hour.

By routing requests through the **`litellm-agents` container (`:4001`)** mounted with a dedicated **GCP Service Account JSON key**:
1. **Zero Token Expiration:** LiteLLM automatically refreshes Google Cloud IAM tokens in the background.
2. **Unified OpenAI-Compatible Endpoint:** Exposes `http://localhost:4001/v1` with model alias `glm-5.2` (and `glm-5.2-maas`).
3. **1M Context Window & Agentic Tool-Calling:** Supports long-horizon multi-file coding, repository traversal, and native function calling.

---

## 2. Prerequisites (Google Cloud IAM)

Ensure your Vertex AI Service Account (or user account) has the **Vertex AI User** role on your GCP project:

```bash
gcloud projects add-iam-policy-binding your-gcp-project-id \
    --member="serviceAccount:vertex-ai-sa@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

---

## 3. LiteLLM Configuration (`litellm-agents/litellm_config.yaml`)

```yaml
model_list:
  # Zhipu AI GLM-5.2 (Vertex AI MaaS - 1M context, agentic coding & reasoning)
  - model_name: glm-5.2
    litellm_params:
      model: vertex_ai/zai-org/glm-5.2-maas
      vertex_project: "os.environ/GCP_PROJECT_ID"
      vertex_location: "global"

router_settings:
  model_group_alias:
    "glm-5.2-maas": "glm-5.2"
```

---

## 4. Configuring Cline / Roo Code in VS Code

1. Open **Cline** or **Roo Code** settings in VS Code (`code-server` on port `9080`).
2. Configure:
   - **API Provider:** `OpenAI Compatible`
   - **Base URL:** `http://localhost:4001/v1`
   - **API Key:** Your `LITELLM_MASTER_KEY` from `.env`
   - **Model ID:** `glm-5.2`

---

## 5. Direct Vertex AI OpenAI Endpoint Verification (Optional cURL Test)

To test the upstream Vertex AI MaaS endpoint directly using `gcloud`:

```bash
ENDPOINT="aiplatform.googleapis.com"
REGION="global"
PROJECT_ID="your-gcp-project-id"

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  "https://${ENDPOINT}/v1/projects/${PROJECT_ID}/locations/${REGION}/endpoints/openapi/chat/completions" \
  -d '{
    "model": "zai-org/glm-5.2-maas",
    "stream": false,
    "messages": [{"role": "user", "content": "Write a concise Python healthcheck function."}]
  }'
```

---

## 6. GLM-5.2 Architecture & Benchmark Highlights

- **1M Token Context Window:** Sustains long-horizon multi-file software engineering and architectural analysis.
- **IndexShare Sparse Attention:** Reuses indexers across sparse attention layers, reducing per-token FLOPs by **2.9×** at 1M context length, paired with Multi-Token Prediction (MTP) speculative decoding.
- **Key Benchmarks:**
  - **SWE-bench Pro:** `62.1%`
  - **Terminal Bench 2.1:** `81.0%` (`82.7%` best harness)
  - **FrontierSWE:** `74.4%`
  - **MCP-Atlas (Agentic Tool Use):** `76.8%`
  - **GPQA-Diamond:** `91.2%` | **AIME 2026:** `99.2%`
- **License:** MIT Open-Source License (Copyright © 2026 Zhipu AI).
