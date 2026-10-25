#!/bin/bash

# Ensure .env exists, if not, create it from .env.example
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "=========================================================================="
        echo "⚠️  .env file not found. Creating one from .env.example..."
        cp .env.example .env
        echo "Please edit .env with your specific configurations (like GCP_PROJECT_ID)."
        echo "=========================================================================="
    fi
fi

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    source .env
fi

# Generate WEBUI_SECRET_KEY if it's missing or still the default example string
if [ -z "$WEBUI_SECRET_KEY" ] || [ "$WEBUI_SECRET_KEY" = "replace_with_a_secure_random_string" ]; then
    WEBUI_SECRET_KEY=$(head -c 32 /dev/urandom | base64)
    # If .env exists, update it or append to it so the key persists
    if [ -f ".env" ]; then
        if grep -q "^WEBUI_SECRET_KEY=" .env; then
             sed -i "s|^WEBUI_SECRET_KEY=.*|WEBUI_SECRET_KEY=$WEBUI_SECRET_KEY|" .env
        else
             echo "WEBUI_SECRET_KEY=$WEBUI_SECRET_KEY" >> .env
        fi
    fi
fi

# LiteLLM requires a master key; persist it so Open WebUI keeps working on redeploy.
if [ -z "$LITELLM_MASTER_KEY" ] || [ "$LITELLM_MASTER_KEY" = "replace_with_a_secure_random_string" ]; then
    LITELLM_MASTER_KEY="sk-$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
    if [ -f ".env" ]; then
        if grep -q "^LITELLM_MASTER_KEY=" .env; then
            sed -i "s|^LITELLM_MASTER_KEY=.*|LITELLM_MASTER_KEY=$LITELLM_MASTER_KEY|" .env
        else
            echo "LITELLM_MASTER_KEY=$LITELLM_MASTER_KEY" >> .env
        fi
    fi
fi
if [ -f ".env" ]; then
    chmod 600 .env
fi

# Set default credentials file if not set in .env
GCP_CREDENTIALS_FILE="${GCP_CREDENTIALS_FILE:-credentials.json}"

# Ensure required directories and files exist
if [ ! -f "$GCP_CREDENTIALS_FILE" ]; then
    echo "=========================================================================="
    echo "⚠️  $GCP_CREDENTIALS_FILE not found in the current directory!"
    echo "Please provide your GCP Service Account JSON key or update .env"
    echo "=========================================================================="
    exit 1
fi
chmod 600 "$GCP_CREDENTIALS_FILE"

# Storage path for RAG data (on RAID)
RAID_STORAGE="${DATA_STORAGE_PATH:-/mnt/raid1/podman-volumes/open-webui-data}"
mkdir -p "$RAID_STORAGE"

# Pinned image versions (bump these to upgrade)
OPEN_WEBUI_IMAGE="${OPEN_WEBUI_IMAGE:-ghcr.io/open-webui/open-webui:v0.12.3}"
LITELLM_IMAGE="${LITELLM_IMAGE:-ghcr.io/berriai/litellm:main-latest}"
TIKA_IMAGE="${TIKA_IMAGE:-docker.io/apache/tika:latest}"

# Network & Port bindings (loaded from .env with safe defaults)
DOCKER_NETWORK="${DOCKER_NETWORK:-private-ai-net}"
OPEN_WEBUI_BIND_IP="${OPEN_WEBUI_BIND_IP:-0.0.0.0}"
OPEN_WEBUI_PORT="${OPEN_WEBUI_PORT:-8080}"
LITELLM_BIND_IP="${LITELLM_BIND_IP:-0.0.0.0}"
LITELLM_PORT="${LITELLM_PORT:-4000}"
TIKA_BIND_IP="${TIKA_BIND_IP:-127.0.0.1}"
TIKA_PORT="${TIKA_PORT:-9998}"

# Optional CAD service (built locally from ./cad-service). Failure to build
# or start it is non-fatal: the rest of the stack keeps running.
CAD_SERVICE_IMAGE="cad-service:local"
CAD_SERVICE_ENABLED="${CAD_SERVICE_ENABLED:-1}"

echo "Setting up network ($DOCKER_NETWORK)..."
docker network create "$DOCKER_NETWORK" 2>/dev/null || true

echo "Pulling latest images..."
docker pull "$OPEN_WEBUI_IMAGE"
docker pull "$LITELLM_IMAGE"
docker pull "$TIKA_IMAGE"

echo "Starting LiteLLM (Vertex AI & Mistral Proxy) on ${LITELLM_BIND_IP}:${LITELLM_PORT}..."
docker rm -f litellm 2>/dev/null || true
docker run -d \
    --name litellm \
    --network "$DOCKER_NETWORK" \
    --restart unless-stopped \
    -p "${LITELLM_BIND_IP}:${LITELLM_PORT}:4000" \
    -v $(pwd)/litellm_config.yaml:/app/config.yaml:ro \
    -v $(pwd)/"$GCP_CREDENTIALS_FILE":/app/credentials.json:ro \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
    -e GCP_PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}" \
    -e LITELLM_MASTER_KEY="$LITELLM_MASTER_KEY" \
    -e MISTRAL_API_KEY="${MISTRAL_API_KEY:-}" \
    -e OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}" \
    -e NVIDIA_API_KEY="${NVIDIA_API_KEY:-}" \
    "$LITELLM_IMAGE" \
    --config /app/config.yaml ${LITELLM_EXTRA_ARGS:-}

echo "Waiting for LiteLLM to be ready..."
for i in $(seq 1 45); do
    if curl -fsS "http://127.0.0.1:${LITELLM_PORT}/health/liveliness" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "Starting Apache Tika (OCR / PDF extraction) on ${TIKA_BIND_IP}:${TIKA_PORT}..."
docker rm -f tika 2>/dev/null || true
docker run -d \
    --name tika \
    --network "$DOCKER_NETWORK" \
    --restart unless-stopped \
    -p "${TIKA_BIND_IP}:${TIKA_PORT}:9998" \
    "$TIKA_IMAGE"

echo "Starting Open WebUI (with RAID storage at $RAID_STORAGE) on ${OPEN_WEBUI_BIND_IP}:${OPEN_WEBUI_PORT}..."
docker rm -f open-webui 2>/dev/null || true

docker run -d \
    --name open-webui \
    --network "$DOCKER_NETWORK" \
    --restart unless-stopped \
    -p "${OPEN_WEBUI_BIND_IP}:${OPEN_WEBUI_PORT}:8080" \
    -v $RAID_STORAGE:/app/backend/data \
    -e CONTENT_EXTRACTION_ENGINE=tika \
    -e TIKA_SERVER_URL=http://tika:9998 \
    -e RAG_PDF_EXTRACT_IMAGES=False \
    -e RAG_EMBEDDING_ENGINE=openai \
    -e RAG_OPENAI_API_BASE_URL=http://litellm:4000/v1 \
    -e RAG_OPENAI_API_KEY="$LITELLM_MASTER_KEY" \
    -e OPENAI_API_BASE_URL=http://litellm:4000/v1 \
    -e OPENAI_API_KEY="$LITELLM_MASTER_KEY" \
    -e RAG_EMBEDDING_MODEL=text-embedding-004 \
    -e BYPASS_EMBEDDING_AND_RETRIEVAL=True \
    -e WEBUI_SECRET_KEY="$WEBUI_SECRET_KEY" \
    "$OPEN_WEBUI_IMAGE"

echo "Waiting for Open WebUI to be ready..."
for i in $(seq 1 30); do
    if docker exec open-webui python3 -c "import sys; sys.exit(0)" 2>/dev/null; then
        break
    fi
    sleep 2
done
echo "Installing missing Open WebUI dependencies (PDF OCR, Document generation)..."
docker exec open-webui pip install rapidocr python-docx python-pptx openpyxl pandas --quiet 2>&1 | grep -E 'Successfully|already|ERROR' || true

# ---------------- Optional: CAD service (DWG/DXF + XLSX) ----------------
# Non-fatal: any error here does not abort the deploy of the main stack.
CAD_SERVICE_STATUS="skipped"
if [ "$CAD_SERVICE_ENABLED" = "1" ] && [ -f "cad-service/Dockerfile" ]; then
    echo "Building CAD service image (cad-service/)..."
    if docker build -t "$CAD_SERVICE_IMAGE" cad-service/ >/tmp/cad-build.log 2>&1; then
        echo "Starting CAD service (port 8090, internal only)..."
        docker rm -f cad-service 2>/dev/null || true
        if docker run -d \
            --name cad-service \
            --network "$DOCKER_NETWORK" \
            --restart unless-stopped \
            -e MAX_UPLOAD_MB=500 \
            "$CAD_SERVICE_IMAGE" >/tmp/cad-run.log 2>&1; then
            CAD_SERVICE_STATUS="up"
        else
            CAD_SERVICE_STATUS="start_failed"
            echo "⚠️  CAD service failed to start (see /tmp/cad-run.log). Main stack unaffected."
        fi
    else
        CAD_SERVICE_STATUS="build_failed"
        echo "⚠️  CAD service image failed to build (see /tmp/cad-build.log). Main stack unaffected."
    fi
else
    echo "CAD service disabled (CAD_SERVICE_ENABLED=$CAD_SERVICE_ENABLED, dockerfile present: $([ -f cad-service/Dockerfile ] && echo yes || echo no))"
fi

echo "=========================================================================="
echo "✅ Open WebUI, LiteLLM and Tika started successfully!"
echo "✅ RAG data stored on RAID at: $RAID_STORAGE"
echo "✅ Models available: Gemini 3.1 Pro Preview, Gemini 3.8 Flash, Codestral (codestral-2508), Ministral 14B"
echo "ℹ️  CAD service status: $CAD_SERVICE_STATUS  (see CAD_README.md)"
echo "Access the beautiful interface at: http://localhost:${OPEN_WEBUI_PORT}"

echo "It might take a minute for Open WebUI to fully start."
echo "To view logs:"
echo "  Open WebUI:  docker logs -f open-webui"
echo "  LiteLLM:     docker logs -f litellm"
echo "  Tika OCR:    docker logs -f tika"
echo "  CAD service: docker logs -f cad-service   (if running)"
echo "=========================================================================="