#!/bin/bash
# =============================================================================
# Standalone Deployment Script for `litellm-agents`
# Dedicated LiteLLM gateway for Cline, Roo Code, and IDE coding agents.
# Isolated from the main Private AI Hub stack (`litellm`).
# All ports, bind IPs, credentials, and API keys are loaded from `.env`.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Ensure local .env exists; if neither local nor root .env exists, bootstrap from .env.example
if [ ! -f "$SCRIPT_DIR/.env" ] && [ ! -f "$ROOT_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        echo "=========================================================================="
        echo "⚠️  .env file not found. Creating $SCRIPT_DIR/.env from .env.example..."
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        chmod 600 "$SCRIPT_DIR/.env"
        echo "Please edit $SCRIPT_DIR/.env with your specific configurations."
        echo "=========================================================================="
    fi
fi

# 1. Load shared secrets/config from root .env first (if present)
if [ -f "$ROOT_DIR/.env" ]; then
    chmod 600 "$ROOT_DIR/.env" 2>/dev/null || true
    source "$ROOT_DIR/.env"
fi

# 2. Load local overrides from litellm-agents/.env (if present)
if [ -f "$SCRIPT_DIR/.env" ]; then
    chmod 600 "$SCRIPT_DIR/.env" 2>/dev/null || true
    source "$SCRIPT_DIR/.env"
fi

CONTAINER_NAME="${LITELLM_AGENTS_CONTAINER:-litellm-agents}"
BIND_IP="${LITELLM_AGENTS_BIND_IP:-0.0.0.0}"
HOST_PORT="${LITELLM_AGENTS_PORT:-4001}"
DOCKER_NETWORK="${DOCKER_NETWORK:-private-ai-net}"
LITELLM_IMAGE="${LITELLM_IMAGE:-ghcr.io/berriai/litellm:main-latest}"
CONFIG_FILE="$SCRIPT_DIR/litellm_config.yaml"

# Auto-generate LITELLM_MASTER_KEY if missing or still set to placeholder
if [ -z "$LITELLM_MASTER_KEY" ] || [ "$LITELLM_MASTER_KEY" = "replace_with_a_secure_random_string" ]; then
    LITELLM_MASTER_KEY="sk-$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
    TARGET_ENV="$SCRIPT_DIR/.env"
    [ ! -f "$TARGET_ENV" ] && [ -f "$ROOT_DIR/.env" ] && TARGET_ENV="$ROOT_DIR/.env"
    if [ -f "$TARGET_ENV" ]; then
        if grep -q "^LITELLM_MASTER_KEY=" "$TARGET_ENV"; then
            sed -i "s|^LITELLM_MASTER_KEY=.*|LITELLM_MASTER_KEY=$LITELLM_MASTER_KEY|" "$TARGET_ENV"
        else
            echo "LITELLM_MASTER_KEY=$LITELLM_MASTER_KEY" >> "$TARGET_ENV"
        fi
        chmod 600 "$TARGET_ENV"
    fi
fi

# Resolve GCP credentials path (check local folder first, then root folder)
GCP_CREDENTIALS_FILE="${GCP_CREDENTIALS_FILE:-credentials.json}"
if [ -f "$SCRIPT_DIR/$GCP_CREDENTIALS_FILE" ]; then
    RESOLVED_CREDS="$SCRIPT_DIR/$GCP_CREDENTIALS_FILE"
elif [ -f "$ROOT_DIR/$GCP_CREDENTIALS_FILE" ]; then
    RESOLVED_CREDS="$ROOT_DIR/$GCP_CREDENTIALS_FILE"
elif [ -f "$GCP_CREDENTIALS_FILE" ]; then
    RESOLVED_CREDS="$GCP_CREDENTIALS_FILE"
else
    echo "=========================================================================="
    echo "⚠️  GCP credentials file '$GCP_CREDENTIALS_FILE' not found!"
    echo "Checked: $SCRIPT_DIR/$GCP_CREDENTIALS_FILE and $ROOT_DIR/$GCP_CREDENTIALS_FILE"
    echo "=========================================================================="
    exit 1
fi
chmod 600 "$RESOLVED_CREDS" 2>/dev/null || true

echo "Ensuring network '$DOCKER_NETWORK' exists..."
docker network create "$DOCKER_NETWORK" 2>/dev/null || true

echo "Starting dedicated coding gateway '$CONTAINER_NAME' on ${BIND_IP}:${HOST_PORT}..."
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
docker run -d \
    --name "$CONTAINER_NAME" \
    --network "$DOCKER_NETWORK" \
    --restart unless-stopped \
    -p "${BIND_IP}:${HOST_PORT}:4000" \
    -v "$CONFIG_FILE":/app/config.yaml:ro \
    -v "$RESOLVED_CREDS":/app/credentials.json:ro \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
    -e GCP_PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}" \
    -e LITELLM_MASTER_KEY="$LITELLM_MASTER_KEY" \
    -e MISTRAL_API_KEY="${MISTRAL_API_KEY:-}" \
    -e OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}" \
    -e NVIDIA_API_KEY="${NVIDIA_API_KEY:-}" \
    "$LITELLM_IMAGE" \
    --config /app/config.yaml ${LITELLM_EXTRA_ARGS:-}

echo "Waiting for $CONTAINER_NAME to become ready on port $HOST_PORT..."
for i in $(seq 1 45); do
    if curl -fsS "http://127.0.0.1:${HOST_PORT}/health/liveliness" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "=========================================================================="
echo "✅ $CONTAINER_NAME is UP on http://${BIND_IP}:${HOST_PORT}/v1"
echo "✅ Config mounted: $CONFIG_FILE"
echo "✅ Credentials:    $RESOLVED_CREDS"
echo "ℹ️  View logs:      docker logs -f $CONTAINER_NAME"
echo "ℹ️  Fast reload:    docker restart $CONTAINER_NAME"
echo "=========================================================================="

