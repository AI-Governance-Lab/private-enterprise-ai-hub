[Anglais](README.md) | [Roumain](README.ro.md) | [Français](README.fr.md)

---

# Hub d'IA d'entreprise privée 🏢🤖

Un assistant IA complet et auto-hébergé utilisant **Open WebUI**, **LiteLLM** et **Google Vertex AI (Gemini 3.8 Flash + Gemini 3.1 Pro Preview)**. Conçu pour offrir une évolutivité et une confidentialité de niveau entreprise en déchargeant les calculs LLM vers Google Cloud, tout en conservant l'ensemble des données sensibles, des documents et de l'historique des discussions entièrement sous votre contrôle sur votre propre infrastructure.

## 🚀 Fonctionnalités clés

- **💬 Belle interface Web :** Interface utilisateur similaire à ChatGPT via Open WebUI
- **🌐 Recherche Web en temps réel :** Recherche Internet intégrée via DuckDuckGo (Open WebUI) + ancrage Google Search (LiteLLM/Vertex AI)
- **📚 RAG local (Retrieval-Augmented Generation) :** Téléversez des PDF et des documents ; l'IA effectue des recherches et les cite à l'aide de **text-embedding-004 de Google** (basé sur le cloud, aucune surcharge de processeur local)
- **💾 Historique complet des conversations :** Toutes les conversations sont enregistrées localement sur RAID 1 ; totalement privées
- **🤖 Hub multi-modèles (Google Vertex AI + Mistral AI) :** 
  - **Codestral (codestral-2508)** (Codestral 2508) — spécialisé pour le code, le refactoring, le FIM, contexte de 256k (Roo Code / Cline / Open WebUI)
  - **Gemini 3.1 Pro Preview** (Gemini 3.1 Pro Preview) — raisonnement avancé, requêtes complexes
  - **Gemini 3.8 Flash** (Gemini 3.8 Flash) — réponses instantanées, 1 à 3 secondes, parfait pour un usage quotidien
  - **Ministral 14B** (Ministral 14B) — polyvalent, modèle d'IA européen rapide
  - *Détails complets et guide de configuration d'IDE : [litellm.md](litellm.md)*
- **📄 Traitement intelligent des PDF :** OCR automatique via Apache Tika (PDF numérisés, images dans les documents)
- ** Rapprochement CAD & XLSX (optionnel) :** Extraction des surfaces depuis AutoCAD `.dwg`/`.dxf`, export vers Excel, rapprochement avec les tables de référence cadastrales — conçu pour les flux de travail liés aux expropriations routières. Voir [CAD_README.md](CAD_README.md).
- **🔐 Isolation multi-utilisateurs :** Chaque utilisateur ne voit que ses propres fichiers ; panneau d'administration pour la configuration
- **🚀 Démarrage automatique :** Le service Systemd assure le redémarrage des conteneurs après un redémarrage du serveur
- **🔐 Authentification sécurisée :** Identifiants GCP Service Account ; aucune clé API stockée dans le code
- **🐳 Basé sur Docker :** Déploiement facile ; tout s'exécute dans des conteneurs

---

## 📋 Au sommaire (mis à jour en octobre 2026)

### Versions épinglées actuelles

| Composant | Image / Paquet | Tag / Version | Notes |
|-----------|-----------------|---------------|-------|
| **Open WebUI** | `ghcr.io/open-webui/open-webui` | `v0.12.3` | Version stable épinglée (Port 8080) |
| **LiteLLM** | `ghcr.io/berriai/litellm` | `main-latest` | Tag glissant (mise à jour automatique lors du pull, Port 4000) |
| **Apache Tika** | `docker.io/apache/tika` | `latest` | Tag glissant (mise à jour automatique lors du pull, Port 9998) |
| **code-server (VS Code)** | RPM natif (`coder/code-server`) | `v4.137.0+` | IDE web + Cline AI (Port 9080) |

Consultez [Gestion des versions et mises à niveau](#-version-management--upgrades) ci-dessous pour le flux de travail complet permettant de modifier ces versions.

### Nouveaux composants ajoutés

**Modèles multi-LLM :**
- **Codestral (codestral-2508)** (Codestral 2508) — Modèle de code spécialisé (contexte de 256k), agent IA pour IDE (Roo Code / Cline)
- **Gemini 3.1 Pro Preview** (Gemini 3.1 Pro Preview) — Raisonnement approfondi, problèmes complexes, génération de code
- **Gemini 3.8 Flash** (Gemini 3.8 Flash) — Réponses instantanées (1-3 s), recherche web, conversation quotidienne
- **Ministral 14B** (Ministral 14B) — LLM européen rapide pour le raisonnement général et la conversation multilingue

**Traitement intelligent des documents :**
- **Apache Tika** — OCR et extraction de texte à partir de PDF numérisés, d'images et de documents complexes
- **Google text-embedding-004** — Embeddings basés sur le cloud (768 dimensions) remplaçant les modèles locaux gourmands en CPU
  - Aucun blocage du CPU lors du téléversement de documents
  - Recherche sémantique plus rapide et plus précise

**Gestion multi-utilisateurs :**
- **Utilisateur administrateur** — Accès complet à la configuration du système et aux fichiers de tous les utilisateurs
- **Utilisateurs standards** — Ne voient que leurs propres fichiers ; ne peuvent pas accéder aux documents des autres utilisateurs
- **Partage des modèles de l'espace de travail** — Tous les utilisateurs peuvent voir et utiliser les modèles LLM disponibles

**Fiabilité du système & réseau :**
- **Démarrage automatique systemd** — Les conteneurs redémarrent automatiquement après le redémarrage du serveur
- **Clé de session fixe** — Les sessions du navigateur restent valides entre les redémarrages
- **Stockage RAID 1** — 3,7 To de stockage redondant pour l'historique des conversations et les documents
- **Synchronisation du pare-feu Netavark** — Synchronisation automatisée du pare-feu via systemd (`netavark-firewalld-reload.service`) garantissant le bon fonctionnement continu du DNS des conteneurs Podman lors des rechargements du pare-feu

**Développement & codage à distance :**
- **VS Code Server (code-server)** — IDE basé sur un navigateur sur le port 9080 pour le développement à distance depuis n'importe quel appareil (téléphone, ordinateur portable)
- **Agent IA Cline** — Agent de codage IA intégré à VS Code, se connectant à LiteLLM ou Google Vertex AI (voir [vscode.md](vscode.md))

---

##  Gestion des versions & mises à niveau

Tous les tags des images de conteneur sont déclarés en tant que variables au début de [run.sh](run.sh). Pour modifier une version, modifiez ces variables et réexécutez le script.

### Où les versions sont épinglées

`run.sh` (lines 13–15):

```bash
OPEN_WEBUI_IMAGE="ghcr.io/open-webui/open-webui:v0.11.3"
LITELLM_IMAGE="ghcr.io/berriai/litellm:main-latest"
TIKA_IMAGE="docker.io/apache/tika:latest"
```

`run.sh` always calls `docker pull` on each image before recreating containers, so a re-run with unchanged variables refreshes rolling tags (`main-latest`, `latest`) and a re-run with a bumped `OPEN_WEBUI_IMAGE` downloads and deploys the new pinned version.

### Historique des versions d'Open WebUI dans ce déploiement

| Date | De → Vers | Notes |
|------|-----------|-------|
| 2026-09-06 | `main` (0.11.0) → `v0.11.3` | Épinglé sur stable. Corrige un bug de migration de base de données de 0.11.0–0.11.2. |

### Comment mettre à niveau Open WebUI vers une version plus récente

1. Consultez la dernière version stable : <https://github.com/open-webui/open-webui/releases>
2. Lisez les notes de version pour prendre connaissance des changements incompatibles et des avertissements de migration de la base de données.
3. **Sauvegardez le volume de données** (voir [Sauvegarde & Restauration](#-backup--restore) ci-dessous).
4. Modifiez `run.sh` et changez le tag sur la ligne `OPEN_WEBUI_IMAGE` :
   ```bash
   OPEN_WEBUI_IMAGE="ghcr.io/open-webui/open-webui:v0.11.4"
   ```
5. Redéployer : `./run.sh`
6. Vérifier (voir [Vérification post-déploiement](#post-deploy-verification)).

### Sémantique des balises

| Tag | Signification | Utilisation recommandée |
|-----|---------------|-------------------------|
| `vX.Y.Z` | Version stable épinglée (ex. `v0.11.3`) | ✅ Utilisation en production / entreprise. Reproductible. |
| `latest` | Toujours la dernière version stable | Suivi automatique de la version stable ; moins prévisible. |
| `main` | Branche de développement de pointe | Non recommandé ; peut inclure des commits défectueux. |

---

## 🚀 Modes de déploiement & workflow de redéploiement

Trois opérations prises en charge, toutes pilotées par le même `run.sh`.

### Mode 1 — Premier déploiement (nouvelle installation)

Prérequis : `docker` ou `podman` installé, JSON du compte de service GCP prêt, point de montage RAID disponible sur `/mnt/raid1` (ou modifiez le chemin `RAID_STORAGE` dans `run.sh`).

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

Ouvrez http://localhost:8080, créez le compte administrateur.

### Mode 2 — Redéploiement (configuration inchangée, actualiser les images / redémarrer)

Utilisez ceci après avoir modifié `litellm_config.yaml`, après un redémarrage du système, ou pour récupérer les mises à jour rolling-tag pour LiteLLM/Tika.

```bash
cd /opt/private-ai-hub
./run.sh
```

`run.sh` is idempotent: it does `docker rm -f` on existing containers and recreates them. Data on the RAID volume is untouched.

### Mode 3 — Mettre à niveau Open WebUI vers une nouvelle version

Voir [Comment mettre à niveau Open WebUI](#how-to-upgrade-open-webui-to-a-newer-release) ci-dessus. TL;DR :

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

### Vérification post-déploiement

Chaque déploiement devrait se terminer par ces 4 vérifications :

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

Attendu : 3 conteneurs `Up`, la version correspond au tag `OPEN_WEBUI_IMAGE`, HTTP 200, aucun traceback.

### Retour arrière

Si la mise à niveau casse l'application :

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

## 💾 Sauvegarde & restauration

Tout l'état persistant réside dans `/mnt/raid1/podman-volumes/open-webui-data` (base de données SQLite, téléversements, base de données vectorielle, cache). LiteLLM et Tika sont sans état.

**Sauvegarde (peut être exécutée en toute sécurité pendant que les conteneurs sont actifs, mais des instantanés cohérents nécessitent un arrêt) :**

```bash
STAMP=$(date +%Y%m%d-%H%M%S)
docker stop open-webui   # optional but recommended for a consistent snapshot
tar -czf /mnt/raid1/podman-volumes/backups/open-webui-data-$STAMP.tar.gz \
  -C /mnt/raid1/podman-volumes open-webui-data
docker start open-webui
```

**Restaurer :**

```bash
docker stop open-webui
rm -rf /mnt/raid1/podman-volumes/open-webui-data
tar -xzf /mnt/raid1/podman-volumes/backups/open-webui-data-<STAMP>.tar.gz \
  -C /mnt/raid1/podman-volumes
docker start open-webui
```

**Rotation des sauvegardes** (conserver les 5 dernières, exécuter via cron) :

```bash
ls -1t /mnt/raid1/podman-volumes/backups/open-webui-data-*.tar.gz | tail -n +6 | xargs -r rm
```

---

## 📋 Processus de déploiement (ce que fait `run.sh`)

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

## 🏗️ Vue d'ensemble de l'architecture

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

### Flux de données

1. **Requête utilisateur** → Le navigateur envoie un message à Open WebUI
2. **Traitement** → Open WebUI vérifie si une recherche Web est nécessaire
   - Si nécessaire : interroge DuckDuckGo
   - Formate le contexte pour l'IA
3. **Appel API** → Open WebUI envoie une requête compatible OpenAI à LiteLLM (port 4000)
4. **Traduction** → LiteLLM convertit le format OpenAI au format Google Vertex AI
   - Ajoute l'outil Google Search si configuré
   - Inclut les identifiants (JSON de compte de service) via ${GCP_CREDENTIALS_FILE:-credentials.json}
5. **Traitement LLM** → Vertex AI (Gemini 3.8 Flash ou Gemini 3.1 Pro Preview)
   - Recherche éventuellement sur Internet (via l'ancrage Google Search)
   - Génère la réponse
6. **Réponse** → Renvoyée via LiteLLM → Open WebUI → Navigateur
7. **Stockage** → Historique des discussions enregistré localement (persiste après les redémarrages)

### Détails des conteneurs Docker

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

**Communication entre conteneurs :**
- Open WebUI communique avec LiteLLM via le réseau Docker interne (port 4000)
- Seul le port 8080 est exposé au navigateur
- Port 4000 masqué de l'extérieur ; non accessible depuis Internet
- Toutes les requêtes passent par : Navigateur → Open WebUI → LiteLLM → Vertex AI

---

## 🛠️ Instructions d'installation

### Prérequis

- Docker & Docker Compose (ou Podman)
- Projet GCP avec Vertex AI activé
- Fichier d'identifiants JSON du compte de service (par défaut : credentials.json, modifiable via GCP_CREDENTIALS_FILE dans .env)
- Système Linux avec Podman/Docker
- Au moins 8 Go de RAM (16 Go+ recommandés pour l'indexation de documents volumineux)
- Facultatif : stockage externe RAID/NAS pour les documents

### 1. Configuration des identifiants GCP

1. Accédez à [Google Cloud Console](https://console.cloud.google.com/)
2. Créez ou sélectionnez votre projet GCP
3. Activez l'API Vertex AI
4. Créez un compte de service :
   - IAM et administration → Comptes de service
   - Créer un compte de service
   - Attribuez le rôle : "Vertex AI User"
5. Créez une clé JSON et téléchargez-la
6. **Enregistrez la clé sous le nom `${GCP_CREDENTIALS_FILE:-credentials.json}` dans le répertoire racine de ce projet** (ou spécifiez son nom via `GCP_CREDENTIALS_FILE` dans un fichier `.env`).

### 2. Configurer LiteLLM avec des modèles

Modifiez `litellm_config.yaml` :

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

**Guide de sélection des modèles :**
- **Gemini 3.1 Pro Preview** → Requêtes complexes, débogage de code, analyse approfondie (temps de réponse de 5 à 30 s)
- **Gemini 3.8 Flash** → Réponses rapides, recherche web, discussion quotidienne (temps de réponse de 1 à 3 s)
- **Artist (Google Imagen 3)** → Génération d'images de haute qualité avec Google Imagen 2 (modèle : `imagen@005`)
- **text-embedding-004** → Utilisé automatiquement pour les embeddings RAG (aucune sélection manuelle requise)

### 3. (Facultatif) Configurer le stockage sur NAS/RAID

Si vous disposez d'un stockage externe NAS ou RAID (par ex., `/mnt/raid1`), le script `run.sh` y stocke automatiquement les données RAG :

```bash
# Default: /mnt/raid1/podman-volumes/open-webui-data
# If path doesn't exist, create it:
mkdir -p /mnt/raid1/podman-volumes/open-webui-data

# run.sh will use this automatically
./run.sh

# Verify storage:
ls -la /mnt/raid1/podman-volumes/open-webui-data/
```

**Avantages du stockage externe :**
- ✅ Sépare les données du disque système
- ✅ Protection RAID pour l'historique des conversations
- ✅ Sauvegardes plus faciles
- ✅ Plus d'espace pour les grandes collections de documents

**Modifier run.sh pour utiliser un chemin personnalisé :**
```bash
# Modify this line in run.sh:
RAID_STORAGE="${DATA_STORAGE_PATH:-/mnt/raid1/podman-volumes/open-webui-data}"  # ← Change path
```

### 4. Déployer

```bash
# Make the deployment script executable
chmod +x run.sh

# Run the deployment
./run.sh
```

Cela va :
- Créer le réseau Docker `private-ai-net`
- Démarrer le proxy LiteLLM (port 4000, interne)
- Démarrer le moteur OCR Tika (port 9998, interne)
- Démarrer Open WebUI (port 8080, accessible)
- Monter un stockage persistant pour l'historique des conversations
- Installer RapidOCR pour une extraction d'images améliorée (optionnel)

### 5. (Recommandé) Démarrage automatique des conteneurs au redémarrage du serveur

Créer un service systemd pour démarrer automatiquement les conteneurs après le redémarrage :

**Créer `/etc/systemd/system/private-ai.service` :**
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

**Activer le service :**
```bash
sudo systemctl daemon-reload
sudo systemctl enable private-ai.service
sudo systemctl start private-ai.service

# Verify status
sudo systemctl status private-ai.service
docker ps  # Should show all 3 containers running
```

**Désormais, les conteneurs démarreront automatiquement après le redémarrage du système !**

### 6. Accéder à l'application

Ouvrez votre navigateur et accédez à :
```
http://localhost:8080
```

**Configuration initiale :**
- Créez un compte administrateur (stocké localement, chiffré)
- Sélectionnez soit "Gemini 3.1 Pro Preview" (meilleure qualité), soit "Gemini 3.8 Flash" (plus rapide)
- Commencez à discuter !

---

## 🔧 Variables d'environnement & configuration

### Configuration d'Open WebUI (définie dans run.sh)

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

**Points clés :**
- `WEBUI_SECRET_KEY` est fixe → les sessions persistent entre les redémarrages ✅
- `text-embedding-004` utilise Google Cloud (aucun CPU local) → embeddings rapides ✅
- `CONTENT_EXTRACTION_ENGINE=tika` → OCR automatique pour les PDF numérisés ✅
- `RAG_PDF_EXTRACT_IMAGES=False` → ignore le RapidOCR local lent ; Tika gère les images ✅

### Configuration de LiteLLM (litellm_config.yaml)

3 modèles configurés :
1. **Gemini 3.1 Pro Preview** - Gemini 3.1 Pro Preview (analyse complexe)
2. **Gemini 3.8 Flash** - Gemini 3.8 Flash (réponses rapides)
3. **text-embedding-004** - embeddings GCP pour le RAG

Tous les modèles ont l'ancrage avec la recherche Google activé.

---

## 💻 Comment ça fonctionne

### Discuter avec la recherche Web

1. **Activer la recherche Web :** Cliquez sur le bouton de recherche dans Open WebUI avant de poser votre question
2. **Requête Open WebUI → DuckDuckGo :** Recherche sur le Web à l'aide de DuckDuckGo
3. **Contexte transmis au LLM :** Les résultats de recherche sont inclus dans le prompt
4. **Réponse du LLM :** Gemini 3.8 Flash (ou 3.1 Pro Preview) génère une réponse avec des citations

### Ancrage avec la recherche Google dans Vertex AI

De plus, les deux modèles Gemini ont accès à l'**ancrage Google Search** configuré dans LiteLLM :
- Lorsque LiteLLM envoie des requêtes, il inclut le paramètre `tools: [googleSearch: {}]`
- Vertex AI peut effectuer des recherches sur Google de manière autonome s'il le juge nécessaire
- Fournit des informations en temps réel et une vérification des faits

### RAG sur documents locaux

1. **Téléversement du document :** Cliquez sur « Upload » dans Open WebUI ; sélectionnez un fichier PDF ou texte
2. **Traitement :** Le document est extrait (texte ou OCR si numérisé) via Tika
3. **Vectorisation :** Google text-embedding-004 crée des vecteurs à 768 dimensions
4. **Recherche dans le chat :** Faites référence au document par son nom dans votre requête
5. **Accès par l'IA :** Le LLM reçoit des fragments du document en guise de contexte
6. **Citations :** Les réponses indiquent d'où proviennent les informations

#### Pipeline de traitement PDF (avec Tika OCR)

**Types de PDF pris en charge :**
- ✅ **PDF textuels** (interrogeables) → Tika extrait directement le texte
- ✅ **PDF numérisés** (images) → Tika exécute l'OCR pour extraire le texte
- ✅ **PDF mixtes** (texte + images) → Tika traite toutes les couches
- ✅ **Formats complexes** (multicolonnes, tableaux) → Tika gère la mise en page

**Étapes de traitement :**
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

#### Comment fonctionne la recherche RAG (étape par étape)

**Phase 2 : Requête et récupération**
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

**Phase 3 : Réponse du LLM**
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

## 📂 Stockage et emplacements des fichiers

### À l'intérieur des volumes Docker

**Volume open-webui-data :**
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

**Sur votre machine hôte :**
```bash
# Find where Docker stores the volume
docker volume inspect open-webui-data
# Output shows: "Mountpoint": "/var/lib/docker/volumes/open-webui-data/_data"

# View uploaded files (as root)
sudo ls -la /var/lib/docker/volumes/open-webui-data/_data/uploads/

# Extract a file (example: backup)
sudo cp /var/lib/docker/volumes/open-webui-data/_data/uploads/file.pdf ~/backup/
```

### Schéma de la base de données (tables pertinentes)

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

### Comment accéder aux fichiers par programmation

**À l'intérieur du conteneur :**
```bash
docker exec open-webui ls -la /app/backend/data/uploads/
```

**Sauvegarder tous les téléversements :**
```bash
docker run --rm -v open-webui-data:/data \
  -v ~/backup:/backup \
  alpine cp -r /data/uploads/ /backup/
```

**Interroger directement les embeddings :**
```bash
docker exec open-webui sqlite3 /app/backend/data/webui.db \
  "SELECT file_name, content FROM document LIMIT 5;"
```

---

## 🔍 Utilisation du RAG en pratique

### Exemple : Documents internes de l'entreprise

**Configuration :**
1. Téléversez : `policies.pdf`, `org_chart.xlsx`, `procedures.md`
2. Open WebUI les indexe automatiquement

**Requête de l'utilisateur :**
```
"What's the vacation policy?"
```

**Dans les coulisses :**
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

**Réponse du LLM :**
```
According to company policy, employees receive 20 days of vacation 
annually, plus national holidays [1]. Contact HR for exceptions [1].
```

### Avancé : Recherche multi-documents

**Téléverser les fichiers :**
- `Q1_Report.pdf`
- `Q2_Report.pdf`
- `Budget_2026.xlsx`

**Requête :** "Quelle a été la tendance du chiffre d'affaires du T1 au T2 ?"

**RAG récupère :** les sections pertinentes des deux rapports du T1 et du T2 automatiquement

---

## ⚙️ Configuration RAG (Paramètres administrateur)

Accès via le panneau d'administration Open WebUI :

```
Settings → Retrieval → RAG Configuration
```

**Configuration actuelle (utilisant GCP text-embedding-004) :**
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

**Conseils d'optimisation :**
- **Échec avec les PDF numérisés ?** Vérifiez que Tika est en cours d'exécution : `docker logs tika`
- **Embeddings lents ?** Vérifiez la connectivité GCP : `docker logs litellm | grep "text-embedding-004"`
- **Documents volumineux ?** Augmentez `chunk_size` (ex. 2000)
- **Trop de résultats ?** Réduisez `top_k` (ex. 2)
- **Contenu pertinent manquant ?** Réduisez `relevance_threshold`

---

## 🚀 Limites et solutions de contournement du RAG

| Problème | Cause | Solution de contournement |
|---|---|---|
| « Document non trouvé » | Fichier non téléversé ou mauvaise référence | Téléverser le fichier, puis le référencer par son nom exact |
| Texte du PDF numérisé vide | Le PDF est composé d'images, l'OCR de Tika a échoué | Vérifier les journaux de Tika : `docker logs tika` |
| PDF chiffré rejeté | Le PDF est protégé par mot de passe | Déchiffrer localement d'abord : `qpdf --decrypt input.pdf output.pdf` |
| Résultats non pertinents | Mauvais découpage en blocs (chunks) ou faible pertinence | Découper manuellement le document, téléverser sous forme de fichiers distincts |
| Recherche lente | Latence réseau vers GCP (text-embedding-004) | Normal ; les embeddings prennent 1 à 2 secondes par lot |
| Perdu après redémarrage | Volume non persisté | Toujours utiliser des volumes montés (par défaut dans run.sh) |
| Extraction du PDF vide | Le serveur Tika n'est pas en cours d'exécution ou s'est arrêté brutalement | Redémarrer : `docker restart tika` |

---

## 📊 Stockage & Performances

**Utilisation du disque :**
- Open WebUI de base : ~500 Mo
- Par fichier téléversé : 1 à 10 fois la taille du fichier (métadonnées + embeddings)
- Index SQLite : ~100 Mo pour 1 000 documents
- Stockage RAID : 3,7 To disponibles (sur `/mnt/raid1`)

**Performances des embeddings (avec GCP text-embedding-004) :**
- Génération des embeddings : 1-2 secondes (dans le cloud, aucun CPU local nécessaire)
- Recherche par similarité : 50-500 ms (scan complet SQLite)
- Récupération du contexte du document : <100 ms
- **Avantage :** Décharge le calcul des embeddings ; libère le CPU local pour d'autres tâches

**Performance des requêtes :**
- Avec Gemini 3.1 Pro Preview : 5-30 secondes (raisonnement complexe)
- Avec Gemini 3.8 Flash : 1-3 secondes (réponses rapides)

**Optimisation :**
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

## 🔄 Bonnes pratiques RAG

### Isolation des fichiers multi-utilisateurs

**Modèle de sécurité :**

Chaque fichier téléversé est étiqueté avec `user_id` :
```sql
file table:
  id: 88f922e4-..., user_id: user_a, filename: budget.pdf
  id: 92g033f5-..., user_id: user_b, filename: roadmap.docx

document table (RAG):
  collection_name: ..., user_id: user_a, content: "Budget Q1..."
  collection_name: ..., user_id: user_b, content: "Roadmap 2026..."
```

**Isolation appliquée :**
- ✅ L'utilisateur A interroge `/api/retrieval/files/` → Obtient uniquement les fichiers de l'utilisateur A
- ✅ L'utilisateur B interroge `/api/retrieval/files/` → Obtient uniquement les fichiers de l'utilisateur B
- ✅ L'interface utilisateur masque les documents des autres utilisateurs
- ✅ Le contexte RAG inclut uniquement les documents de l'utilisateur actuel

**Modèle de menace :**

| Scénario | Risque | Atténuation |
|----------|------|-----------|
| L'utilisateur A accède à l'interface utilisateur | Faible | Isolation des fichiers au niveau de l'API |
| L'administrateur accède à SQLite | Élevé | L'administrateur a un accès complet à la base de données |
| Quelqu'un obtient le jeton administrateur | Élevé | Renouveler immédiatement le mot de passe |
| Injection SQL dans Open WebUI | Moyen | Corrigé dans les dernières versions |

**Bonnes pratiques :**
- Utiliser un mot de passe administrateur fort
- Ne pas partager le compte administrateur
- Exécuter Open WebUI derrière un proxy d'authentification s'il est exposé à Internet
- Surveiller les permissions du fichier SQLite : `sudo ls -la /var/lib/docker/volumes/open-webui-data/_data/webui.db`



---

## 🔍 Modèle : "Gemini 3.1 Pro Preview" & "Gemini 3.8 Flash"

Les deux modèles sont configurés avec le même prompt système :

**Prompt système :**
> "Tu es l'assistant de la famille. Tu aides pour tout, bon à tout faire, concernant la maison, la famille, l'école, les informations générales, la programmation, les devoirs.
> 
> Tu as accès à Google Search et tu peux rechercher des informations actuelles sur Internet en temps réel. Lorsque quelqu'un te pose des questions sur l'actualité, la météo, les prix, les événements récents ou toute information susceptible de changer, utilise Google Search pour fournir des réponses exactes et à jour."

**Quand l'utiliser :**
- **Gemini 3.1 Pro Preview** — Problèmes complexes, débogage de code, recherche, lorsque vous avez besoin d'un raisonnement approfondi
- **Gemini 3.8 Flash** — Questions du quotidien, réponses rapides, recherche web, chat avec des documents

**Capacités (les deux modèles) :**
- Recherche web (DuckDuckGo + ancrage Google Search)
- Téléversement de fichiers & RAG (avec GCP text-embedding-004)
- Vision (compréhension d'images)
- Interprétation de code
- Informations en temps réel

---

## 📁 Structure du projet

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

## 🚨 Dépannage

### "Erreur : outil 'search' non trouvé"
- **Cause :** La recherche Web n'était pas configurée dans Open WebUI
- **Solution :** Panneau d'administration → Paramètres → Recherche Web → Activer DuckDuckGo

### "Connexion refusée sur le port 4000"
- **Cause :** Le conteneur LiteLLM n'a pas pu démarrer
- **Vérification :** `docker logs litellm`
- **Problème courant :** `credentials.json` manquant ou invalide (ou le fichier défini via votre `.env`)

### "Impossible d'accéder à Vertex AI"
- **Cause :** Autorisations du compte de service ou projet GCP non configurés correctement
- **Solution :**
  - Vérifiez que `${GCP_CREDENTIALS_FILE:-credentials.json}` (ou votre fichier d'identifiants personnalisé) se trouve à la racine du projet
  - Assurez-vous que le compte de service dispose du rôle "Vertex AI User" (pour `${GCP_CREDENTIALS_FILE:-credentials.json}`)
  - Vérifiez que l'ID de projet GCP correspond à `litellm_config.yaml`

### "L'historique des discussions ne persiste pas"
- **Cause :** Le volume Open WebUI n'est pas monté correctement
- **Solution :** Vérifier le montage RAID : `ls -la /mnt/raid1/podman-volumes/open-webui-data/`
- S'il est vide, redémarrer avec `./run.sh`

### "Le téléversement du PDF prend trop de temps / délai d'attente dépassé"
- **Cause :** Le serveur Tika ne répond pas ou l'OCR traite un document volumineux
- **Vérification :** 
  ```bash
  docker logs tika  # See OCR progress
  docker ps | grep tika  # Verify container is running
  ```
- **Solution :** Donner plus de temps à Tika (il s'initialise lors du premier PDF)
- **Si Tika plante :** `docker logs tika -f` pour voir l'erreur détaillée

### "Le téléversement de PDF est très lent et l'utilisation du processeur est élevée"
- **Cause :** Open WebUI utilise le moteur `RapidOCR` par défaut au lieu de `Tika`. Cela peut se produire si le paramètre dans le panneau d'administration est incorrect.
- **Solution :**
  1. Allez dans **Panneau d'administration** -> **Paramètres** -> **Récupération**.
  2. Trouvez le paramètre **Moteur d'extraction de contenu**.
  3. Changez-le de `default` à `Tika` et enregistrez.

### "Le contenu du PDF apparaît vide après le téléversement"
- **Causes :**
   1. **PDF chiffré :** Tika ne peut pas extraire le contenu de PDF protégés par mot de passe
   2. **Format complexe :** Numérisé à une résolution inhabituelle
   3. **Tika n'est pas en cours d'exécution :** Le conteneur n'a pas pu démarrer
- **Solution pour les PDF chiffrés :**
  ```bash
  # Decrypt locally first using qpdf
  qpdf --decrypt --password-is-hex-string=XXXXXXXX input.pdf output.pdf
  # Then upload output.pdf
  ```
- **Vérifier que Tika fonctionne :**
  ```bash
  docker exec tika curl -s http://localhost:9998/version
  # Should return Tika version info
  ```

### "Erreurs de l'API d'embedding ou lenteur des embeddings"
- **Cause :** Point de terminaison Google text-embedding-004 inaccessible
- **Vérification :**
  ```bash
  docker logs open-webui | grep "embedding"
  ```
- **Correction :**
  - Vérifier que les identifiants GCP sont valides
  - Vérifier la variable d'environnement `RAG_EMBEDDING_MODEL=text-embedding-004`
  - S'assurer que LiteLLM peut accéder à Google Cloud (connectivité réseau)

### "Les conteneurs ne démarrent pas au redémarrage (boot serveur)"
- **Cause :** Podman ignore `--restart unless-stopped` au démarrage (contrairement à Docker)
- **Correctif appliqué :** Service systemd `private-ai.service` créé et activé
- **Vérification :**
  ```bash
  systemctl status private-ai.service   # Trebuie: enabled + active
  systemctl is-enabled private-ai.service  # Trebuie: enabled
  ```
- **Redémarrage manuel si nécessaire :**
  ```bash
  systemctl start private-ai.service
  # sau
  ./run.sh
  ```

### "Session invalidée après redémarrage du conteneur"
- **Cause :** Clé de session modifiée au redémarrage
- **Statut :** ✅ **RÉSOLU** — WEBUI_SECRET_KEY est désormais fixé dans run.sh
- **Vérification :** Les sessions doivent persister entre les redémarrages de `./run.sh`
- **Remarque :** Si vous utilisez un fichier d'identifiants personnalisé, assurez-vous que `${GCP_CREDENTIALS_FILE:-credentials.json}` est correctement monté

### "Open WebUI affiche toujours l'ancienne version après la mise à niveau"
- **Cause 1 :** Le nouveau tag d'image n'a pas été réellement récupéré (problème réseau temporaire, cache).
- **Cause 2 :** Le conteneur n'a pas été recréé (uniquement redémarré).
- **Solution :**
  ```bash
  docker pull ghcr.io/open-webui/open-webui:<new-tag>
  docker rm -f open-webui
  ./run.sh
  docker exec open-webui cat /app/package.json | grep '"version"'
  ```

### "`docker pull` se bloque à la fin pour les images volumineuses (runtime podman)"
- **Cause :** Podman se fige parfois après "Writing manifest to image destination" pour les images de plusieurs Go.
- **Solution :** Annulez avec Ctrl-C et réessayez directement la même commande `docker pull` (en dehors de `run.sh`). Une fois l'image présente localement, réexécutez `./run.sh`.

### "Échec de la migration de la base de données / l'application ne démarre pas après la mise à niveau"
- **Cause :** Migration Alembic ignorée ou corrompue entre les versions d'Open WebUI.
- **Solution :**
  1. Vérifiez les logs pour identifier la migration en échec : `docker logs open-webui 2>&1 | grep -iE 'alembic|migration|error'`
  2. Restaurez la sauvegarde antérieure à la mise à niveau (voir [Rollback](#rollback)).
  3. Signalez l'erreur de migration en amont si elle se reproduit sur une instance propre.

### "Open WebUI: Server Connection Error / Model not found"
- **Cause :** Après une commande `firewall-cmd --reload` (par exemple lors de l'ouverture de ports sur le serveur), `firewalld` sur CentOS Stream 9 réinitialise les règles dynamiques Netavark. L'interface `podman1` et le sous-réseau des conteneurs `10.89.0.0/24` se retrouvent sous la zone par défaut `public`, qui bloque le port 53 (DNS interne `aardvark-dns` sur `10.89.0.1:53`). Dans les logs de `open-webui` apparaît :
  ```text
  Cannot connect to host litellm:4000 [Temporary failure in name resolution]
  Model '' was not found
  ```
- **Correctif appliqué définitivement :**
  1. Ajout du réseau des conteneurs dans la zone `trusted` :
     ```bash
     sudo firewall-cmd --zone=trusted --add-interface=podman1 --permanent
     sudo firewall-cmd --zone=trusted --add-source=10.89.0.0/24 --permanent
     sudo firewall-cmd --reload
     ```
  2. Activation du service officiel de synchronisation automatique Netavark lors des événements de rechargement du pare-feu :
     ```bash
     sudo systemctl enable --now netavark-firewalld-reload.service
     ```
  3. Redémarrage du conteneur WebUI : `podman restart open-webui` (ou `./run.sh`).

### "Conflit de port 8080 (VS Code / code-server et Open WebUI)"
- **Cause :** Open WebUI et `code-server` utilisent tous deux par défaut le port 8080.
- **Solution :** `code-server` a été configuré sur le port `9080` dans `~/.config/code-server/config.yaml` (`bind-addr: 0.0.0.0:9080`), le port 9080 a été ouvert dans le pare-feu, et le service a été redémarré avec `sudo systemctl restart code-server@root`. Voir le guide complet dans [vscode.md](vscode.md).

---

##  Gestion des utilisateurs & contrôle d'accès

### Création et gestion des utilisateurs

**Utilisateur administrateur (Accès complet) :**
- Peut accéder aux paramètres du système
- Peut voir les fichiers et l'historique des conversations de tous les utilisateurs
- Peut configurer les modèles LLM et les paramètres RAG
- Peut gérer les comptes et les rôles des utilisateurs

**Utilisateurs standard (isolation des fichiers) :**
- Peuvent uniquement voir leurs propres documents téléversés
- Peuvent uniquement consulter leur propre historique de discussion
- Peuvent accéder à tous les modèles LLM disponibles (Gemini 3.1 Pro Preview + Flash)
- **Ne peuvent pas voir ni accéder aux fichiers des autres utilisateurs**

### Configuration de plusieurs utilisateurs

1. **Premier utilisateur = Administrateur :**
   ```bash
   Open WebUI → Create account → Auto-becomes admin
   Example: marian.ropota@gmail.com
   ```

2. **Ajouter des utilisateurs supplémentaires :**
   ```bash
   Admin panel → Settings → Users → Add User
   They are automatically "regular users" (non-admin)
   ```

3. **Vérifier le rôle de l'utilisateur (via la base de données) :**
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

4. **Modifier le rôle d'un utilisateur (si nécessaire) :**
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

### Isolation des fichiers dans la base de données

**Comment cela fonctionne :**
- Chaque utilisateur a un `user_id` unique dans SQLite
- Tous les fichiers téléversés sont tagués avec `user_id`
- Requêtes RAG filtrées par `user_id`
- Historique des conversations filtré par `user_id`

**Exemple :**
```sql
-- When admin queries database
SELECT filename FROM file WHERE user_id = 123  -- All of user 123's files

-- When user 123 queries
SELECT filename FROM file WHERE user_id = 123  -- Only their files (auto-filtered)
```

### Partage de modèles d'espace de travail multi-utilisateur

Tous les utilisateurs peuvent voir et utiliser les mêmes modèles d'espace de travail :
- Gemini 3.1 Pro Preview (pour les analyses complexes)
- Gemini 3.8 Flash (pour les discussions rapides)
- text-embedding-004 (utilisé automatiquement pour le RAG)

**Configuration :**
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

## 🔧 Paramètres administrateur

Accédez au panneau d'administration via l'interface utilisateur d'Open WebUI (icône Paramètres si vous êtes connecté en tant qu'administrateur).

**Paramètres clés :**
- **Recherche Web :** Activée (DuckDuckGo)
- **Confirmation de recherche :** Désactivée (les recherches s'effectuent automatiquement)
- **Paramètres du modèle :** Le prompt système inclut la disponibilité de Google Search
- **RAG :** Configuré avec Google text-embedding-004 (embeddings basés sur le cloud)
- **Traitement des PDF :** Tika OCR activé pour les PDF numérisés
- **Isolation des utilisateurs :** Accès aux fichiers contrôlé par rôle utilisateur
- **Persistance de session :** Une WEBUI_SECRET_KEY fixe empêche la déconnexion lors d'un redémarrage

### Important : clé de session fixe

La variable d'environnement `WEBUI_SECRET_KEY` est fixée dans `run.sh` :
```bash
WEBUI_SECRET_KEY=replace_with_a_secure_random_string
```

Les sessions persistent entre les redémarrages de `./run.sh` sans forcer la reconnexion.

---

## 🔍 Surveillance et maintenance

### Vérifier l'état du conteneur

```bash
docker ps  # Should show open-webui, litellm, tika
```

### Afficher les journaux du conteneur

```bash
docker logs open-webui -f     # Open WebUI logs
docker logs litellm -f        # LiteLLM proxy logs
docker logs tika -f           # Tika OCR logs
```

### Vérification de la base de données et du stockage

```bash
# Database size
docker exec open-webui du -h /app/backend/data/webui.db

# User files storage
docker exec open-webui du -sh /app/backend/data/uploads/

# Vector embeddings storage
docker exec open-webui du -sh /app/backend/data/vector_db/
```

### Redémarrer les conteneurs

```bash
./run.sh                              # Restart all containers
sudo systemctl restart private-ai.service  # Via systemd
```

---

## 📊 Utilisation des ressources

- **RAM :** ~2 Go (Open WebUI) + surcharge réseau
- **Stockage :** ~5 Go de base + variable (historique des conversations, documents)
- **CPU :** Traitement local minimal (la majeure partie du travail étant déléguée à Google Cloud)
- **Bande passante :** Dépend de l'utilisation du LLM et des recherches web

---

##  Pour les développeurs : structure et architecture du projet

### Aucun code personnalisé requis

Ce projet **n'inclut pas de code source** — il s'agit d'un **déploiement basé uniquement sur la configuration** :

| Composant | Rôle | Source |
|-----------|------|--------|
| **run.sh** | Orchestration de conteneurs | Votre dépôt (bash simple) |
| **litellm_config.yaml** | Configuration de LiteLLM | Votre dépôt (YAML) |
| **${GCP_CREDENTIALS_FILE:-credentials.json}** | Authentification GCP | Votre projet GCP (JSON) |
| **Conteneur Open WebUI** | Image préconstruite : `ghcr.io/open-webui/open-webui:v0.11.3` (figée ; modifier `run.sh` pour changer) | Docker Hub / GHCR |
| **Conteneur LiteLLM** | Image préconstruite : `ghcr.io/berriai/litellm:main-latest` (continue) | Docker Hub / GHCR |

**Vous fournissez la configuration. Les images Docker apportent du code précompilé.**

### Ce que fait chaque conteneur

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

### Flux de données (technique)

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

### Frontières de sécurité

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
```

### Détails clés de l'implémentation

**Isolation des ports :**
- Port 8080 : Open WebUI (vous y accédez)
- Port 4000 : proxy LiteLLM (interne à Docker uniquement)
- Aucun port exposé par défaut sauf le 8080

**Montages de volumes :**
- `open-webui-data` : Persiste la base de données SQLite + les fichiers téléversés
- `litellm_config.yaml` : Lecture seule, monté dans le conteneur LiteLLM
- `${GCP_CREDENTIALS_FILE:-credentials.json}` : Lecture seule, monté dans le conteneur LiteLLM

**Variables d'environnement (à l'intérieur du conteneur LiteLLM) :**
```bash
GOOGLE_APPLICATION_CREDENTIALS=/app/${GCP_CREDENTIALS_FILE:-credentials.json}
# (set by run.sh)
```

**Réseau :**
- `private-ai-net` : réseau Docker reliant les deux conteneurs
- Résolution DNS : `open-webui:8080` accessible depuis le conteneur `litellm`
- Aucun accès réseau externe sauf vers les API Google Cloud

---

##  Configuration multi-utilisateur & isolation des fichiers

### Rôles des utilisateurs

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

### Détails de l'isolement

Les fichiers de chaque utilisateur sont étiquetés avec `user_id` dans SQLite :
```sql
FILE table:  id, user_id, filename, file_path
DOCUMENT table (RAG): content, user_id, embedding
```

**Filtrage des requêtes RAG :**
- Lorsqu'un utilisateur recherche des documents, seuls ses documents sont vectorisés et récupérés
- Aucune contamination croisée entre les utilisateurs

---

### Classification des données

| Données | Emplacement | Exposition | Notes |
|------|----------|----------|-------|
| Historique des conversations | SQLite local | Aucune | Uniquement sur votre machine |
| Documents | Volume local | Aucune | Jamais téléversés vers le cloud |
| Embeddings | Volume local | Aucune | Générés localement |
| Prompts | En transit vers Google | Minimale | Supprimés après la réponse |
| Identifiants | Fichier local | Aucune | Jamais exposés en externe |
| Configuration LiteLLM | Fichier local | Aucune | Monté en lecture seule |

### Modèle de menace

**❌ Ne peut pas se produire :**
- Google accédant à votre historique de discussion
- Conteneurs transmettant vos données vers l'extérieur
- credentials.json exposé dans les logs
- Données de discussion persistées dans le cloud

**⚠️ Peut se produire si :**
- Vous exposez le port 8080 sur Internet sans authentification
- Vous commitez credentials.json dans git
- Vous `docker push` le conteneur vers un registre public
- Le trafic réseau n'est pas chiffré

**✅ Atténué par :**
- Déploiement local (isolé du réseau par défaut)
- TLS vers les API Google
- Authentification par compte de service (pas de clés API dans le code)
- Identifiants montés en lecture seule

### Bonnes pratiques

1. **Garder les identifiants privés**
   ```bash
   # Add to .gitignore
   echo "credentials.json" >> .gitignore
   echo ".env" >> .gitignore
   ```

2. **Ne pas exposer le port 8080**
   ```bash
   # ❌ DON'T do this (unless intentional)
   docker run -p 0.0.0.0:8080:8080  # Exposes to internet
   
   # ✅ Default (safe)
   docker run -p 127.0.0.1:8080:8080  # Localhost only
   ```

3. **Surveiller les coûts GCP**
   - Consulter [la tarification de Vertex AI](https://cloud.google.com/vertex-ai/pricing)
   - Configurer des alertes de facturation dans la console GCP

4. **Renouveler périodiquement les identifiants**
   - Supprimer les anciennes clés de compte de service
   - En générer de nouvelles dans la console GCP
   - Mettre à jour credentials.json

---

## 📝 Commandes

**Consultez [🚀 Modes de déploiement et workflow de redéploiement](#-deploy-modes--redeploy-workflow) pour les recettes complètes de premier déploiement, redéploiement, mise à niveau et retour arrière.** Cette section liste les commandes quotidiennes.

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

### Systemd Autostart (démarrage automatique au boot)

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

### Test rapide

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

## 🌍 Documentation multilingue

Ce projet prend en charge la documentation en plusieurs langues :
- **Anglais** (par défaut) : `*.md`
- **Roumain** : `*.ro.md`
- **Français** : `*.fr.md`

**Règle de traduction :** Lors de la traduction de la documentation, **tous les commentaires de code doivent rester en anglais**. Seul le texte Markdown environnant doit être traduit.

---

##  Prochaines étapes

- Personnalisez le prompt système dans les paramètres Admin
- Importez vos propres documents pour le RAG
- Explorez différentes requêtes pour tester la recherche web
- Surveillez les coûts dans Google Cloud Console

Profitez de votre assistant IA privé ! 🤖

- **16-Sep-2026 :** (ou la date actuelle) J'ai synchronisé et complètement intégré les nouveaux outils `CAD Tools (v0.3.0)` pour le support XLSX avec un téléchargement propre.

- **06-Sep-2026 :** J'ai synchronisé et complètement intégré les nouveaux outils `CAD Tools (v0.3.0)` pour une prise en charge native de XLSX dans Open WebUI avec un téléchargement propre.
