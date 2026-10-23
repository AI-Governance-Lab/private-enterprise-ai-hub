[English](CAD_README.md) | [Română](CAD_README.ro.md) | [Français](CAD_README.fr.md)

---

# CAD Service — DWG/DXF ⇄ XLSX pour les expropriations routières 🛣️📐

Module optionnel ajouté au stack principal ([README.md](README.fr.md)) qui extrait les surfaces (parcelles) d'un dessin AutoCAD, génère des fichiers XLSX et vérifie la cohérence par rapport au tableau cadastral de référence.

Il s'installe et se lance via le même script `run.sh`. Si le build ou le démarrage échoue, **le reste du stack continue de fonctionner** — voir [Fail-safe design](#fail-safe-design) ci-dessous.

---

## 🎯 Ce qu'il fait

Trois flux principaux, commandés depuis le chat via Gemini Pro/Flash :

1. **Découvrir** ce que contient le DWG (`cad_introspect`) — le modèle reçoit la liste des calques (layers) et des attributs de bloc, puis vous demande « quels sont les calques des parcelles ? » et « quelle colonne d'Excel sert de clé ? ». Rien n'est codé en dur.
2. **Extraire** les surfaces (`cad_extract`, `cad_to_excel`) — superficies calculées en m² / ha / km², avec totaux. Vous pouvez recevoir le résultat sous forme de JSON dans le chat ou de fichier XLSX téléchargeable.
3. **Vérifier** (`cad_reconcile`) — compare les surfaces DWG avec un XLSX de référence ; génère un rapport avec les écarts supérieurs à la tolérance, les parcelles manquantes et les parcelles fantômes.

Formats supportés : **`.dwg`** (AutoCAD 2018+ testé via libredwg ; mise à niveau vers ODA File Converter en cas de fichiers problématiques — voir ci-dessous) et **`.dxf`** (ASCII ou binaire).

---

## 🏗️ Architecture


```
Browser ──► Open WebUI ──► LLM (Gemini via LiteLLM) ──► tool cad_*
                                                            │
                                                            ▼ HTTP intern
                                                    ┌─────────────────┐
                                                    │  cad-service    │
                                                    │  FastAPI :8090  │
                                                    │  ezdxf +        │
                                                    │  libredwg +     │
                                                    │  openpyxl       │
                                                    └─────────────────┘
```


- Conteneur `cad-service` sur le réseau `private-ai-net` (non exposé à l'extérieur — aucun port publié).
- Communique uniquement via le DNS interne : `http://cad-service:8090`.
- Stateless : aucun volume persistant, ne conserve aucune donnée.
- Les tools Python s'exécutent dans le processus Open WebUI et effectuent des requêtes HTTP vers `cad-service`.

---

## 📁 Fichiers ajoutés


```
cad-service/
├── Dockerfile             # Python 3.11 + libredwg-tools + ezdxf + openpyxl
├── requirements.txt
├── app.py                 # FastAPI: /health /introspect /extract /export-excel /reconcile
└── samples/               # Fișiere de test (DXF + XLSX) — vezi samples/README.md
    ├── README.md
    ├── generate.py
    ├── expropriere_sample.dxf
    └── expropriere_sample.xlsx

openwebui-tools/
└── cad_tool.py            # Se importă manual în Open WebUI: Workspace → Tools → Import
```


`run.sh` a été enrichi d'une section optionnelle (activée par défaut) qui build l'image localement et démarre le conteneur.

---

## 🚀 Déploiement

### First-time (le conteneur est ajouté à un stack existant)


```bash
cd /opt/private-enterprise-ai-hub
./run.sh
```


Le script :
1. exécute `docker build -t cad-service:local cad-service/`
2. démarre le conteneur sur le réseau `private-ai-net`
3. affiche à la fin `CAD service status: up | build_failed | start_failed | skipped`

### Désactivation

Si vous souhaitez l'ignorer temporairement :


```bash
CAD_SERVICE_ENABLED=0 ./run.sh
```


### Rebuild après modifications du code


```bash
docker build -t cad-service:local /opt/private-enterprise-ai-hub/cad-service/
docker rm -f cad-service
./run.sh
```


### Importer le tool dans Open WebUI (une seule fois)

1. Ouvrez `http://localhost:8080`
2. Workspace → **Tools** → **Import from file**
3. Téléversez `openwebui-tools/cad_tool.py`
4. Activez le tool pour les modèles **Gemini Pro** et/ou **AI Assistant Flash** :
   Admin → Models → *Model* → Tools → cochez `CAD Tools`

---## 📤 Comment l'utilisateur téléverse les fichiers

Le modèle **ne reçoit pas d'URL ou d'ID de fichier** — Open WebUI injecte automatiquement le kwarg spécial `__files__` dans les tools lorsqu'il y a des fichiers joints au message. Les tools CAD sélectionnent automatiquement les fichiers selon leur extension (`.dwg`/`.dxf` pour le dessin, `.xlsx` pour la référence).

**Étapes utilisateur :**

1. Dans le chat, joindre les fichiers au message avec 📎 (Attach) :
   - Pour extract/introspect/to-excel : un seul fichier `.dwg` ou `.dxf`.
   - Pour reconcile : **les deux** — `.dwg` (ou `.dxf`) et `.xlsx` — sur le **même** message.
2. Dans le message, saisir la demande souhaitée (ex. : « scanne les calques » ou « vérifie les surfaces avec l'Excel »).
3. Le modèle appelle le tool approprié sans qu'il soit nécessaire de lui fournir des ID ou des URL.

**Fichiers acceptés :**
- Open WebUI accepte n'importe quelle extension by default (`RAG_ALLOWED_FILE_EXTENSIONS=[]`, sans limite de taille).
- Les fichiers sont enregistrés sur le RAID sous `/mnt/raid1/podman-volumes/open-webui-data/uploads/{uuid}_{filename}` — persistants entre les redémarrages.

**Recommandation pour les fichiers CAD volumineux :**
- Lors de l'upload, cliquer sur le fichier → basculer **« Bypass Embedding and Retrieval »** → ON. Cela empêche Open WebUI de tenter une indexation RAG sur des binaires CAD (ce qui n'a pas de sens et polluerait la vector DB avec des octets bruts). Le tool CAD a un accès direct au fichier sur le disque indépendamment de ce paramètre.

**Quand l'utilisateur ne téléverse qu'un seul des 2 fichiers attendus :**

Le modèle reçoit un message d'erreur structuré, pas une exception :

```json
{
  "error": "missing_files",
  "action": "reconcile",
  "need": ["an .xlsx reference table"],
  "attached_now": ["km_12+300.dwg"],
  "hint": "Ask the user to attach both files to the same chat message."
}
```

Le modèle demande à l'utilisateur le fichier manquant dans la langue de la conversation.

---

## 🧪 Vérification post-déploiement


```bash
# 1. Is container running?
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep cad-service

# 2. Health check OK? (from internal network)
docker exec open-webui curl -s http://cad-service:8090/health | python3 -m json.tool

# Expected response:
# {
#   "status": "ok",
#   "converter": "dwg2dxf",
#   "converter_ok": true,
#   "converter_version": "libredwg 0.12.5 ...",
#   "ezdxf_version": "1.3.5",
#   "max_upload_mb": 500
# }
```


Si le `status` est `degraded`, le convertisseur DWG ne répond pas — seul DXF fonctionne jusqu'à résolution (voir troubleshooting).

---

## 🔌 API — endpoints

Tous avec un payload `multipart/form-data`. Port interne **8090** (non exposé publiquement).

### `GET /health`

Health-check + versions.

### `POST /introspect`

**Form :** `file: UploadFile`

**Réponse (extrait) :**

```json
{
  "filename": "planse_km_12+300_12+800.dwg",
  "dxf_version": "AC1032",
  "insunits_code": 6, "meters_per_unit": 1.0, "unit_label": "m",
  "layer_count": 47,
  "layers": [
    {"name": "S_EXPROPRIERE_DEFINITIV", "total": 132, "hatch": 128, "lwpolyline_closed": 4, "insert": 0, ...},
    {"name": "PARCELA_CADASTRAL", "total": 128, "insert": 128, ...}
  ],
  "block_attribute_keys": [
    {"tag": "NR_PARCELA", "count": 128},
    {"tag": "SUPRAFATA_MP", "count": 128},
    {"tag": "PROPRIETAR", "count": 128}
  ]
}
```


### `POST /extract`

**Form :**
- `file: UploadFile`
- `layers` = `"*"` (glob séparé par des virgules, ex. : `"S_EXPROPRIERE_*,PARCELA_*"`)
- `source_types` = `"block_attr,hatch,lwpolyline_closed,polyline_closed"` — types d'entités ciblés
- `unit` = `"m2" | "ha" | "km2"`

Réponse : JSON avec `areas[]`, `total_area`, `count`.

### `POST /export-excel`

Mêmes inputs que `/extract` + `sheet_name`. Réponse : fichier **XLSX** avec `Content-Disposition: attachment`.

### `POST /reconcile`

**Form :**
- `dwg: UploadFile`
- `xlsx: UploadFile`
- `xlsx_key_column` — nom de la colonne clé dans le XLSX (ex. : `Nr_parcela`)
- `xlsx_area_column` — colonne contenant la surface (ex. : `Suprafata_masurata_mp`)
- `dwg_key_attribute` — tag de bloc contenant l'identifiant de la parcelle (ex. : `NR_PARCELA`)
- `layers`, `source_types`, `unit` (comme pour extract)
- `xlsx_sheet` (optionnel ; vide = active sheet)
- `tolerance_pct` (par défaut `0.5`)
- `tolerance_abs` (par défaut `0.01`)

Réponse : totaux, comptages, `matched_ok`, `matched_diff` (hors tolérance), `missing_in_dwg`, `missing_in_xlsx`. Les listes sont limitées à 200 lignes.

---

## 💬 Exemple de flux type dans le chat


```
User: [📎 atașează km_12+300.dwg]  [📎 atașează expropriere_km_12+300.xlsx]
      Verifică ariile.

Model: [apelează cad_introspect() — nu-i dă niciun argument;
        tool-ul găsește .dwg-ul singur din __files__]

       "Desenul are 47 de layere. Am găsit 4 care par să conțină suprafețe:
        - S_EXPROPRIERE_DEFINITIV (132 hatch-uri)
        - S_EXPROPRIERE_TEMPORAR  (56 hatch-uri)
        - PARCELA_CADASTRAL       (128 blocuri cu atribute NR_PARCELA, SUPRAFATA_MP)
        - CONSTRUCTII_EXISTENTE   (12 hatch-uri)

        Care sunt layerele parcelelor de verificat? Bănuiesc PARCELA_CADASTRAL — confirmi?
        Îmi trebuie și numele coloanelor din Excel: care e cheia (Nr_parcela?)
        și care e aria (Suprafata_masurata_mp?)."

User: da, PARCELA_CADASTRAL. In excel: Nr_parcela + Suprafata_masurata_mp.
      toleranta 0.1%.

Model: [apelează cad_reconcile(
          layers='PARCELA_CADASTRAL',
          dwg_key_attribute='NR_PARCELA',
          xlsx_key_column='Nr_parcela',
          xlsx_area_column='Suprafata_masurata_mp',
          tolerance_pct=0.1
        ) — tool-ul găsește ambele fișiere singur]

        "Verificat 128 parcele:
         - ✅ 121 OK (sub 0.1% diferență)
         - ⚠️ 5 diferă peste toleranță:
             #A7-023: XLSX=1240.50 m², DWG=1247.83 m² (Δ +0.59%)
             #A7-041: XLSX=890.10 m²,  DWG=901.44 m²  (Δ +1.27%)
             ...
         - ❌ 2 lipsesc din DWG: A7-055, A7-091
         Total: XLSX 187,432 m² vs DWG 187,890 m² (Δ +458 m²)"
```


---## 🛡️ Conception Fail-safe

**Ce qui se passe si `cad-service` est indisponible (down) :**

1. `run.sh` affiche `CAD service status: build_failed` ou `start_failed`, mais **le reste du stack démarre normalement**.
2. Lorsque le modèle appelle un tool CAD, il reçoit un JSON d'erreur explicite :
   
```json
   {
     "error": "cad_service_unavailable",
     "action": "introspect",
     "detail": "ConnectError: [Errno -2] Name or service not known",
     "hint": "Restul chat-ului funcționează. Verifică: docker ps | grep cad-service"
   }
   ```

3. Le modèle indiquera à l'utilisateur : « le service CAD ne répond pas pour le moment » et continuera normalement avec le reste des requêtes (chat, RAG, web search, Vertex AI).

**Comment vérifier l'état :**

```bash
docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep cad
docker logs cad-service --tail 50
```


---

## 🚨 Troubleshooting

### `CAD service status: build_failed`
- **Cause :** échec d'apt/pip ou build context manquant
- **Vérifier :** `cat /tmp/cad-build.log | tail -50`
- **Correctif courant :** exécutez `docker system prune -f` pour libérer de l'espace, puis relancez `./run.sh`

### `CAD service status: start_failed`
- **Cause :** le port interne est occupé ou l'image n'a pas été construite
- **Vérifier :** `cat /tmp/cad-run.log`

### `converter_ok: false` dans /health
- **Cause :** `dwg2dxf` (libredwg) est manquant dans l'image
- **Correctif :** reconstruire l'image — `docker build -t cad-service:local cad-service/`

### `500 DWG->DXF conversion failed`
- **Cause :** fichier DWG récent (AC1032 / AC1035) que libredwg ne parvient pas à lire
- **Correctif rapide :** enregistrez depuis AutoCAD au format DXF ASCII ou en DWG 2013 et réessayez
- **Correctif définitif :** mise à niveau vers ODA File Converter (voir plus bas)

### Les surfaces sont erronées (trop grandes ou trop petites)
- **Cause :** les unités du modèle DWG ne correspondent pas à celles attendues. Le cadastre RO est habituellement en mètres, mais certains travaillent en mm.
- **Vérifier :** la réponse `/introspect` contient `insunits_code` et `unit_label`. S'il s'agit de `mm` (`insunits_code=4`), la mise à l'échelle s'effectue automatiquement.
- **Si la valeur est `unspecified` (code=0)**, le service suppose qu'il s'agit de mètres. Corrigez en enregistrant le DWG avec la variable `INSUNITS` définie.

### `413 File too large`
- **Cause :** fichier > 500 MB
- **Correctif :** surcharge au déploiement : dans `run.sh`, modifiez `-e MAX_UPLOAD_MB=500` avec la valeur souhaitée et redéployez

### Le tool CAD n'apparaît pas dans le chat
- Vérifiez que vous l'avez bien importé depuis l'UI (Workspace → Tools) — cela ne se fait pas automatiquement
- Vérifiez qu'il est activé pour le modèle utilisé (Admin → Models → *Model* → Tools)

### Le tool répond par `no_matching_file_attached`
- **Cause :** vous avez saisi la commande sans joindre le fichier (ou vous l'avez joint avec une mauvaise extension).
- **Correctif :** cliquez sur le trombone 📎 dans la barre de saisie de message et ajoutez un fichier `.dwg` / `.dxf` (ou `.xlsx` pour le reconcile). Renvoyez le message.

### Le tool répond par `file_not_on_disk`
- **Cause :** WebUI a bien enregistré le file_id, mais le chemin attendu (`/app/backend/data/uploads/{id}_{name}`) n'existe pas.
- **Correctif :** vérifiez le volume dans le container : `docker exec open-webui ls /app/backend/data/uploads/ | grep <id>`. S'il est absent, ré-uploadez-le (l'upload a probablement échoué partiellement).

### Le RAG semble « pollué » après l'upload d'un fichier CAD
- **Cause :** Open WebUI fait passer par défaut tout upload par Tika pour le RAG. Le format DXF ASCII peut générer des chunks de coordonnées brutes.
- **Correctif :** lors de l'upload, cliquez sur le fichier CAD → activez **« Bypass Embedding and Retrieval »**. Le tool CAD fonctionne de toute façon — il ne dépend pas du RAG.### `cad-service` inaccessible ou erreur de résolution depuis Open WebUI (`Temporary failure in name resolution`)
- **Cause :** Le rechargement du pare-feu de l'hôte (`firewall-cmd --reload`) a réinitialisé les règles dynamiques Podman (`netavark`), bloquant les requêtes DNS sur `10.89.0.1:53`.
- **Correctif :** Le réseau Podman a été ajouté à la zone `trusted` du pare-feu, et le service `netavark-firewalld-reload.service` a été activé de manière permanente. Voir la section dédiée au dépannage dans [vscode.md](vscode.fr.md).

---

## ⬆️ Mise à niveau vers ODA File Converter (recommandé pour DWG 2018+)

libredwg fonctionne sur la majorité des fichiers DWG, mais présente un décalage par rapport aux formats très récents. ODA File Converter (Open Design Alliance, gratuit, closed-source) est le standard de l'industrie.

**Étapes :**

1. Téléchargez le `.deb` pour Linux x86_64 depuis :
   <https://www.opendesign.com/guestfiles/oda_file_converter>
   (inscription gratuite requise)
2. Placez le fichier dans `cad-service/` (ex. : `ODAFileConverter_QT6_lnxX64_8.3dll_25.3.deb`)
3. Décommentez le bloc dans `cad-service/Dockerfile` :
   
```dockerfile
   COPY ODAFileConverter_*.deb /tmp/oda.deb
   RUN apt-get update && apt-get install -y --no-install-recommends /tmp/oda.deb \
       xvfb libglu1-mesa && rm -rf /var/lib/apt/lists/* /tmp/oda.deb
   ```

4. Modifiez `app.py` → fonction `_convert_dwg_to_dxf` pour appeler `ODAFileConverter` au lieu de `dwg2dxf`
5. Rebuild + redeploy : `docker build -t cad-service:local cad-service/ && docker rm -f cad-service && ./run.sh`

---

## 🔒 Sécurité & isolation

- Le port 8090 est **uniquement interne** (réseau Docker `private-ai-net`), non exposé à l'extérieur.
- Le service fonctionne en mode stateless, sans volumes, sans credentials.
- Les téléversements résident dans un `tempfile.TemporaryDirectory()` — ils sont supprimés immédiatement après le traitement.
- Aucune donnée ne quitte le serveur (contrairement à LiteLLM qui envoie des prompts à Vertex AI, les outils CAD sont 100% locaux).

---

## 📊 Performances approximatives

Mesuré sur ai-hub-server (2 CPU, 6 GB RAM) :

| Opération | DWG 10 MB | DWG 100 MB | DWG 500 MB |
|---|---|---|---|
| `/introspect` | ~2 s | ~15 s | ~90 s |
| `/extract` (128 parcelles) | ~3 s | ~20 s | ~2 min |
| `/export-excel` | +1 s par rapport à extract | +1 s | +1 s |
| `/reconcile` (128 vs XLSX 128 lignes) | ~4 s | ~22 s | ~2 min |

Le goulot d'étranglement principal est la conversion DWG→DXF. Les fichiers DXF ASCII sont de 3 à 5 fois plus rapides.

### Comment accéder aux fichiers et les télécharger 
Les outils exportent un lien de la forme `[⬇️ nom_fichier_areas_m2.xlsx](/api/v1/files/UUID/content)`.
- Cliquez simplement sur le lien pour télécharger directement le fichier.
- (Les informations techniques d'export en base64 ont été remplacées par un stockage persistant local natif Open WebUI, résolvant l'erreur d'hallucination des modèles).

### Comment accéder aux fichiers et les télécharger
Les outils exportent un lien de la forme `[⬇️ nom_fichier_areas_m2.xlsx](/api/v1/files/UUID/content)`.
- Cliquez simplement sur le lien pour télécharger directement le fichier.
- (Les informations techniques d'export en base64 ont été remplacées par un stockage persistant local natif Open WebUI, résolvant l'erreur d'hallucination des modèles).