[English](cline_config_gcp_login.md) | [Română](cline_config_gcp_login.ro.md) | [Français](cline_config_gcp_login.fr.md)

---

# Guide de Configuration Google Cloud & Vertex AI pour Cline

Ce document décrit la configuration permettant d'utiliser le **Service Account dédié à Vertex AI** **exclusivement dans VS Code / Cline**, tout en conservant le compte utilisateur `developer@your-org.com` par défaut (*default*) dans Google Cloud CLI (`gcloud`).

---

## 🟢 Statut de la configuration : ACTIF & TESTÉ AVEC SUCCÈS (Fonctionne à 100 % ✅)

* **Authentification SA Vertex AI :** **CONFIRMÉE ET VALIDE** (Token généré avec succès sur le projet `your-gcp-project-id`).
* **Compte CLI actif sur le système :** `developer@your-org.com` (Inchangé).
* **Service Account par défaut global :** **DÉSACTIVÉ** (La variable globale a été supprimée de `~/.bashrc`).
* **Isolation :** Complète. Seul le processus VS Code / Cline reçoit la clé du Service Account.

---

## 📌 Détails Techniques

| Paramètre | Valeur |
| :--- | :--- |
| **Chemin de la clé du Service Account (isolé)** | `/path/to/your/vertex-sa-credentials.json` |
| **Nom du Service Account** | `vertex-ai-sa@your-gcp-project-id.iam.gserviceaccount.com` |
| **GCP Project ID** | `your-gcp-project-id` |
| **GCP Region** | `us-central1` |
| **Compte par défaut CLI (`gcloud`)** | `developer@your-org.com` |

---

## 🚀 Comment lancer VS Code avec Cline (Option A - Implémentée)

### Méthode 1 : Utilisation de l'alias dédié (Recommandé)

Les alias suivants ont été configurés dans `~/.bashrc` :


```bash
# Open the private-enterprise-ai-hub project directly with Vertex AI credentials
code-cline

# OR open any other directory with Vertex AI credentials
code-vertex /path/to/folder
```


### Méthode 2 : Commande inline directe


```bash
GOOGLE_APPLICATION_CREDENTIALS="${GCP_CREDENTIALS_FILE:-/path/to/your/vertex-sa-credentials.json}" code /opt/private-enterprise-ai-hub
```


---

## ⚙️ Configuration dans les paramètres de Cline (VS Code)

Une fois VS Code ouvert via l'une des commandes ci-dessus :

1. Cliquez sur **⚙️ Settings** dans le panneau Cline.
2. Définissez **API Provider :** `Google Vertex AI`.
3. Renseignez :
   * **GCP Project ID :** `your-gcp-project-id`
   * **GCP Region :** `us-central1`
   * **Model :** `gemini-2.5-pro` (ou `gemini-2.0-flash` / `gemini-1.5-pro`)
4. Cline s'authentifiera automatiquement à l'aide de la clé SA transmise au démarrage, sans jamais demander de connexion via le navigateur.

---

## 🔒 Pourquoi cette approche fonctionne-t-elle ?

1. **Aucun conflit dans le terminal :** Lorsque vous ouvrez un terminal standard sur le serveur, `gcloud` continue d'utiliser votre compte `developer@your-org.com`.
2. **Aucune expiration de token :** La clé RSA du Service Account est permanente et n'expire pas après quelques heures.
3. **Aucune pollution de l'environnement :** La variable `GOOGLE_APPLICATION_CREDENTIALS` existe **uniquement** à l'intérieur de l'arborescence des processus de VS Code.

---

## 🔍 Vérification rapide du fonctionnement

Pour vérifier si le SA génère des tokens valides sur Vertex AI :


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

*(Le test s'exécute et renvoie : `Autentificare reusita: True`, `Proiect conectat: your-gcp-project-id`)*.


---

## 🌐 Utilisation dans VS Code Web (`code-server` sur le Port 9080)

Si vous utilisez VS Code exécuté directement sur le serveur via `code-server` (accessible depuis le navigateur à `http://<IP_SERVEUR>:9080` conformément à [vscode.md](vscode.fr.md)) :

### 1. Faut-il redémarrer après l'installation de Cline dans code-server ?
* **Le serveur Linux :** **NON**, le serveur ne redémarre pas.
* **Navigateur / VS Code :** En règle générale, l'extension est active immédiatement. Si l'icône Cline n'apparaît pas dans la barre latérale gauche, un simple **rafraîchissement de la page** (`F5` ou `Ctrl+R`) ou `Ctrl+Shift+P` ➡️ **`Developer: Reload Window`** suffit.
* Uniquement si l'extension rencontre des erreurs de mémoire ou des processus bloqués :
  
```bash
  sudo systemctl restart code-server@root
  ```### 2. Options de connexion dans Cline sur code-server :

#### Option A : Via LiteLLM local (Recommandé)
* Panneau Cline ➡️ **⚙️ Settings**
* **API Provider:** `OpenAI Compatible`
* **Base URL:** `http://localhost:4000/v1`
* **API Key:** `dummy`
* **Model ID:** `Gemini 3.8 Flash` ou `Gemini 3.1 Pro Preview`

#### Option B : Directement via Google Cloud Vertex AI
* Panneau Cline ➡️ **⚙️ Settings**
* **API Provider:** `Google Vertex AI`
* **GCP Project ID:** `your-gcp-project-id`
* **GCP Region:** `us-central1`
* **Model:** `gemini-2.5-pro` (ou `gemini-2.0-flash`)
* La clé SA `/path/to/your/vertex-sa-credentials.json` est déjà présente sur le système et validée.