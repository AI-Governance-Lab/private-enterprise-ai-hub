# 💻 Ghid Instalare & Configurare VS Code Server (code-server) & Cline

Acest document descrie instalarea și configurarea **VS Code Web (code-server)** pe serverul CentOS Stream 9 (`ai-hub-server`), configurarea extensiei **Cline**, rezolvarea conflictelor de porturi cu Open WebUI și remedierea incidentului de firewall care a afectat rezoluția DNS a containerelor Podman.

---

## 📋 Cuprins
1. [Prezentare Generală](#-prezentare-generală)
2. [Pasul 1: Instalare code-server](#-pasul-1-instalare-code-server)
3. [Pasul 2: Activare Serviciu Systemd](#-pasul-2-activare-serviciu-systemd)
4. [Pasul 3: Rezolvare Conflict Port (8080 ➡️ 9080)](#-pasul-3-rezolvare-conflict-port-8080-️-9080)
5. [Pasul 4: Configurare Firewall (firewalld)](#-pasul-4-configurare-firewall-firewalld)
6. [Pasul 5: Accesare de pe Rețeaua Locală (Pixel 8, Laptop)](#-pasul-5-accesare-de-pe-rețeaua-locală-pixel-8-laptop)
7. [Asistenții AI: Cline & Roo Code — Configurare, Modele & Alternative](#-asistenții-ai-cline--roo-code--configurare-modele--alternative)
8. [🚨 Post-Mortem & Troubleshooting: Open WebUI "Server Connection Error / Model Not Found"](#-post-mortem--troubleshooting-open-webui-server-connection-error--model-not-found)
9. [🚨 Troubleshooting Webviews: "Could not register service worker" (Cline / Roo Code / Mermaid)](#-eroare-critică-could-not-register-service-worker-securityerror-an-ssl-certificate-error-occurred-when-fetching-the-script)
10. [🚨 Troubleshooting Roo Code: "Could not find ripgrep binary" & "Invalid thought signature"](#-troubleshooting-roo-code-could-not-find-ripgrep-binary--invalid-thought-signature)
11. [Comenzi Rapide de Mentenanță](#-comenzi-rapide-de-mentenanță)

---

## 🌐 Prezentare Generală

* **Software:** `code-server` v4.x (Coder) - rulează VS Code complet în browser.
* **Server OS:** CentOS Stream 9 (Kernel 5.14, arhitectură x86_64).
* **Port alocat:** `9080` (pentru a evita conflictul cu Open WebUI de pe `8080`).
* **Serviciu systemd:** `code-server@root.service`.
* **Utilizare:** Editare fișiere, rulare comenzi în terminal și asistență de codare cu **Cline** direct din rețeaua internă (inclusiv de pe telefon Pixel 8 / tabletă).

---

## 📥 Pasul 1: Instalare code-server

Instalarea se realizează prin scriptul oficial furnizat de Coder, care detectează pachetul RPM potrivit pentru CentOS:

```bash
curl -fsSL https://code-server.dev/install.sh | sh
```

Acesta instalează binarul în `/usr/bin/code-server` și fișierele de bibliotecă în `/usr/lib/code-server`.

---

## ⚙️ Pasul 2: Activare Serviciu Systemd

Activăm și pornim serviciul pentru utilizatorul `root`:

```bash
sudo systemctl enable --now code-server@root
```

Pornirea serviciului generează automat directorul și fișierul de configurare inițial la `~/.config/code-server/config.yaml`.

---

## 🔌 Pasul 3: Rezolvare Conflict Port (8080 ➡️ 9080)

### Problema
Implicit, `code-server` încearcă să asculte pe portul `8080` pe `127.0.0.1`. Însă:
* **Portul 8080** este deja ocupat de containerul **Open WebUI**.
* code-server trebuie să fie accesibil din rețeaua locală (`0.0.0.0`), nu doar localhost.

### Soluția
Edităm fișierul de configurare:
```bash
nano ~/.config/code-server/config.yaml
```

Modificăm fișierul astfel (folosim `cert: false` pentru HTTP curat, evitând erorile de certificat SSL la încărcarea Service Worker-ilor):
```yaml
bind-addr: 0.0.0.0:9080
auth: password
password: [PAROLA_DUMNEAVOASTRA]
cert: false
```

Repornim serviciul pentru a prelua noile setări:
```bash
sudo systemctl restart code-server@root
```

Verificăm că serviciul ascultă pe noul port `9080`:
```bash
sudo ss -tulpn | grep 9080
# Expected result: tcp LISTEN ... *:9080 ... users:(("node",pid=...))
```

---

## 🛡️ Pasul 4: Configurare Firewall (firewalld)

Pentru a permite accesul altor dispozitive din rețeaua locală la portul 9080:

```bash
sudo firewall-cmd --zone=public --add-port=9080/tcp --permanent
sudo firewall-cmd --reload
```

⚠️ **Atenție critică legată de `firewall-cmd --reload`:** Vezi secțiunea de [Troubleshooting](#-post-mortem--troubleshooting-open-webui-server-connection-error--model-not-found) pentru efectul pe care acest reload îl are asupra Podman și cum a fost remediat definitiv.

---

## 📱 Pasul 5: Accesare de pe Rețeaua Locală (Pixel 8, Laptop)

Pentru ca panourile Webview (Cline, Roo Code, Mermaid) să funcționeze corect pe rețeaua locală, browserul trebuie configurat să permită Service Worker-ii pe adresa HTTP a serverului.

### 1. Activare suport Secure Context în Chrome (pe PC și pe Pixel 8) — o singură dată:
1. Deschide o filă nouă în browserul **Chrome** (sau Brave) și tastează în bara de adrese:
   ```text
   chrome://flags/#unsafely-treat-insecure-origin-as-secure
   ```
2. La setarea **"Insecure origins treated as secure"**:
   * Comută din **Disabled** în **Enabled**.
   * În căsuța text apărută, introdu adresa serverului:
     ```text
     http://192.168.7.90:9080
     ```
3. Apasă pe butonul albastru **Relaunch** din colțul din dreapta-jos pentru a reporni Chrome.

### 2. Conectare la code-server:
1. Deschide browserul și accesează:
   ```text
   http://192.168.7.90:9080
   ```
2. Introdu parola configurată în `~/.config/code-server/config.yaml`.
3. **Sfat pentru Pixel 8 / Android:** În Chrome, deschide meniul (trei puncte) și selectează **"Add to Home screen" / "Install app"**. VS Code se va deschide ca o aplicație PWA nativă fullscreen, fără bara de adresă a browserului.

---

## 🤖 Asistenții AI: Cline & Roo Code — Configurare, Modele & Alternative

Atât **Cline**, cât și **Roo Code** (fork-ul avansat al Cline, axat pe multi-mode și autonomie) sunt instalate și complet funcționale pe `code-server`.

Există **două opțiuni principale de conectare** la modelele Gemini de pe server:

---

### Opțiunea 1: Driver Nativ Google Cloud Vertex AI (Recomandat pentru stabilitate maximă)

Roo Code și Cline includ un driver oficial nativ pentru **Google Cloud Vertex AI**. Acesta comunică direct cu Google Cloud (fără intermediar LiteLLM), evitând problemele de translatare a semnăturilor de gândire (*thought signatures*) și oferind o fereastră de context uriașă (1 milion de token-uri).

#### Modele Gemini suportate de driverul nativ:
Driverul nativ recunoaște direct din meniu sau permite introducerea oricărui ID de model Vertex AI:
* **`gemini-2.5-pro`** — Vârful de gamă Google: raționament profund, codare complexă, planificare de arhitectură.
* **`gemini-2.5-flash`** — Model de generație nouă, extrem de rapid și inteligent.
* **`gemini-2.0-flash`** — Modelul standard rapid (1M context, stabil).
* **`gemini-2.0-flash-lite`** — Versiune ultra-economică pentru sarcini simple.
* **`gemini-1.5-pro`** — Context masiv (până la 2 milioane de token-uri).
* **`gemini-1.5-flash`** — Rapid și eficient.
* **Modele Preview / Custom:** Poți introduce manual orice endpoint/model ID din proiect (ex. `gemini-3.1-pro-preview`, `gemini-3.8-flash`).

#### Cum configurezi în Roo Code / Cline:
1. În bara din stânga, fă click pe iconița **Roo Code** (sau **Cline**).
2. Click pe rotița ⚙️ (**Settings**) din colțul dreapta-sus.
3. Completează:
   * **API Provider:** `Google Cloud Vertex AI`
   * **Google Cloud Project ID:** `your-gcp-project-id`
   * **Google Cloud Region:** `us-central1`
   * **Path to Service Account Key File:**
     ```text
     ${GCP_CREDENTIALS_FILE:-/path/to/your/vertex-sa-credentials.json}
     ```
   * **Model:** Selectează `gemini-2.5-pro` sau `gemini-2.0-flash`
4. Click pe **Save**.

---

### Opțiunea 2: Prin LiteLLM Local (OpenAI Compatible)

Folosește proxy-ul LiteLLM care rulează pe server, același care alimentează și Open WebUI.

#### Cum configurezi în Roo Code / Cline:
1. Click pe ⚙️ (**Settings**) în panoul Roo Code sau Cline.
2. Completează:
   * **API Provider:** `OpenAI Compatible`
   * **Base URL:** `http://localhost:4000/v1`
   * **API Key:** `dummy` (sau orice text, ex. `sk-litellm`)
   * **Model ID:**
     * `Gemini 3.8 Flash` — răspunsuri instantanee (1-2 sec)
     * `Gemini 3.1 Pro Preview` — raționament profund
3. Click pe **Save**.

---

### 🌟 Bonus: Configurarea pe Moduri în Roo Code

Roo Code permite setarea de modele diferite pentru moduri diferite:
* **Modul `Code` (scriere și editare fișiere):** Setează-l pe `gemini-2.5-flash` sau `Gemini 3.8 Flash` pentru viteză maximă.
* **Modul `Architect` (analiză proiect, arhitectură, planificare):** Setează-l pe `gemini-2.5-pro` sau `Gemini 3.1 Pro` pentru raționament strategic.
* **Modul `Ask` (întrebări generale despre cod):** Setează-l pe `gemini-2.0-flash` sau `Gemini 3.8 Flash`.

> **💡 Sincronizare automată:** Cline și Roo Code își salvează setările și istoricul în `/root/.local/share/code-server/User/globalStorage/`. La redeschiderea browserului sau reinstalare, setările rămân persistente.


---

## 🚨 Post-Mortem & Troubleshooting: Open WebUI "Server Connection Error / Model Not Found"

### Simptomul observat
Imediat după executarea comenzii:
```bash
sudo firewall-cmd --zone=public --add-port=9080/tcp --permanent
sudo firewall-cmd --reload
```
Aplicația **Open WebUI** (port 8080) a încetat să mai funcționeze corect:
* La trimiterea unui mesaj către `Gemini 3.1 Pro` sau `Gemini 3.8 Flash`, apărea bannerul roșu:
  **`Open WebUI: Server Connection Error`**
* În interfață apărea:
  **`Model "" was not found`**

### Analiza Cauzei Rădăcină (Root Cause)
1. **Netavark vs Firewalld:** Pe CentOS Stream 9, Podman folosește driverul de rețea `netavark` și serverul DNS intern `aardvark-dns` (care ascultă pe `10.89.0.1:53` pe interfața bridge `podman1`).
2. **Efectul comenzii reload:** Comanda `firewall-cmd --reload` golește și reface tabelele `nftables`/`iptables` ale sistemului.
3. **Blocarea DNS-ului:** După reload, interfața `podman1` a rămas neasociată unei zone explicite, intrând sub zona implicită `public`. În zona `public`, portul 53 (DNS) este blocat (`reject with icmpx admin-prohibited`).
4. **Log-urile containerului `open-webui`:**
   ```text
   open_webui.routers.openai:send_get_request - Connection error: Cannot connect to host litellm:4000 [Temporary failure in name resolution]
   open_webui.main:process_chat - Error processing chat payload: Model "" was not found
   ```
   Deoarece Open WebUI nu mai putea rezolva numele DNS intern `litellm`, conexiunea către proxy-ul LLM pica, iar lista de modele dispărea.
5. **Serviciu lipsă la boot:** Serviciul oficial `netavark-firewalld-reload.service` era în starea `disabled`, astfel că la reload-ul firewall-ului regulile Podman nu erau reinstalate automat.

### Soluția Definitivă Aplicată (Fix Permanent)

Pentru a asigura rezistența permanentă la orice viitor `firewall-cmd --reload`, s-au executat următoarele:

#### 1. Includerea rețelei Podman în zona `trusted` a firewall-ului
```bash
sudo firewall-cmd --zone=trusted --add-interface=podman1 --permanent
sudo firewall-cmd --zone=trusted --add-source=10.89.0.0/24 --permanent
sudo firewall-cmd --reload
```
*Traficul de pe interfața `podman1` și din subnetul `10.89.0.0/24` este acum întotdeauna acceptat de firewall.*

#### 2. Activarea serviciului automat de reîncărcare Netavark
```bash
sudo systemctl enable --now netavark-firewalld-reload.service
```
*Acest serviciu de sistem ascultă pe DBus evenimentele emise de firewalld. Oricând se dă `firewall-cmd --reload`, Netavark reaplică instantaneu toate regulile rețelelor de containere.*

#### 3. Repornirea containerului Open WebUI
```bash
podman restart open-webui
```

### Validarea Funcționării
După aplicarea fix-ului:
1. Test de rezoluție internă din containerul `open-webui`:
   ```bash
   podman exec open-webui python3 -c "import socket; print('Resolved litellm to:', socket.gethostbyname('litellm'))"
   # Output: Resolved litellm to: 10.89.0.2  (SUCCESS)
   ```
2. Test apel API LiteLLM din `open-webui`:
   ```bash
   podman exec open-webui python3 -c "import urllib.request; print(urllib.request.urlopen('http://litellm:4000/models').read().decode()[:100])"
   # Output: {"data":[{"id":"Gemini 3.1 Pro Preview"...  (SUCCESS)
   ```
3. Test generare chat prin ambele modele:
   * **Gemini 3.8 Flash:** Răspuns `200 OK`
   * **Gemini 3.1 Pro Preview:** Răspuns `200 OK`

### 🚨 Eroare Critică: "Could not register service worker: SecurityError... An SSL certificate error occurred when fetching the script"

#### Simptom:
La deschiderea panoului **Cline**, **Roo Code** sau **Mermaid**, apare eroarea:
```text
Error loading webview: Error: Could not register service worker: SecurityError: Failed to register a ServiceWorker for scope (...) with script (...): An SSL certificate error occurred when fetching the script..
```
Sau fereastra rămâne complet albă / nu reacționează la click pe setări.

#### Cauza Tehnică (Documentată oficial în Coder / code-server FAQ):
1. Panourile extensiilor (Cline, Roo Code, Mermaid) rulează ca ferestre interne numite **Webviews**.
2. Webview-urile din VS Code au nevoie obligatoriu de un **Service Worker** pentru a încărca scripturile de interfață.
3. Chiar dacă ați acceptat certificatul autogenerat pe HTTPS pentru pagina principală, **motorul Chromium (Chrome pe PC și pe mobil Pixel 8) REFUZĂ din considerente de securitate să înregistreze Service Worker-i descărcați printr-un certificat SSL nesemnat / untrusted**.
4. Pe HTTP simplu (`http://192.168.7.90:9080`), browserul blochează de asemenea Service Worker-ii deoarece consideră adresa IP ca „Insecure Context”.

#### Soluția Oficială & Recomandată (Activare prin flag-ul Chrome):
Pentru a permite browserului să încarce Service Worker-ii pe rețeaua locală fără erori de certificat:

1. **Pe PC sau pe telefonul Pixel 8 (în Google Chrome / Brave):**
   * Deschideți o filă nouă și tastați în bara de adrese:
     ```text
     chrome://flags/#unsafely-treat-insecure-origin-as-secure
     ```
   * La setarea **"Insecure origins treated as secure"**:
     * Comutați pe **Enabled**.
     * În caseta text de dedesubt, introduceți adresa serverului:
       ```text
       http://192.168.7.90:9080
       ```
   * Apăsați butonul albastru **Relaunch** din colțul de jos al browserului pentru a reporni Chrome.

2. **Accesați code-server pe HTTP:**
   * Deschideți: `http://192.168.7.90:9080`
   * `code-server` rulează pe HTTP simplu (`cert: false`), astfel nu va mai exista nicio eroare de certificat SSL.
   * Datorită flag-ului activat, Chrome tratează `http://192.168.7.90:9080` exact ca pe `localhost` (100% securizat).
   * Service Worker-ul se înregistrează instantaneu, iar panourile **Cline**, **Roo Code** și **Mermaid** funcționează perfect.

#### Unde se configurează de fapt Cline / Roo Code:
* **Atenție:** În VS Code, dacă mergeți la `Extensions (Ctrl+Shift+X)` ➡️ `Cline` ➡️ `⚙️ Manage` ➡️ `Extension Settings`, pagina aceea conține doar opțiuni interne de rollout.
* Setările reale ale asistentului AI se fac direct din panoul său:
  1. Click pe **iconița Cline / Roo Code** din bara verticală din stânga.
  2. În partea de sus a panoului, click pe rotița ⚙️ (**Settings**).
  3. Alegeți API Provider: `OpenAI Compatible` cu `http://localhost:4000/v1` (LiteLLM) sau `Google Vertex AI`.

---

## 🚨 Troubleshooting Roo Code: "Could not find ripgrep binary" & "Invalid thought signature"

### 1. Eroarea: "Error listing files: Could not find ripgrep binary"

#### Simptom:
La solicitarea de a scana sau lista fișierele dintr-un folder, Roo Code (sau Cline) afișează:
```text
Error listing files: Could not find ripgrep binary
```

#### Cauza Tehnică:
Extensiile VS Code caută executabilul `ripgrep` (`rg`) în directoarele standard de sistem (`/usr/bin/rg`) sau în calea internă `node_modules/@vscode/ripgrep/bin/rg`. În distribuția RPM a `code-server`, binarul era arhivat sub `@vscode/ripgrep-universal/bin/linux-x64/rg` și lipsea din `$PATH`-ul global.

#### Soluția Aplicată Permanent:
Am creat legături simbolice (symlinks) globale și în directoarele interne ale `code-server`:
```bash
# Global symlinks in PATH
sudo ln -sf /usr/lib/code-server/lib/vscode/node_modules/@vscode/ripgrep-universal/bin/linux-x64/rg /usr/local/bin/rg
sudo ln -sf /usr/lib/code-server/lib/vscode/node_modules/@vscode/ripgrep-universal/bin/linux-x64/rg /usr/bin/rg

# Symlinks for internal paths expected by VS Code extensions
sudo mkdir -p /usr/lib/code-server/lib/vscode/node_modules/@vscode/ripgrep/bin
sudo ln -sf /usr/lib/code-server/lib/vscode/node_modules/@vscode/ripgrep-universal/bin/linux-x64/rg /usr/lib/code-server/lib/vscode/node_modules/@vscode/ripgrep/bin/rg
sudo mkdir -p /usr/lib/code-server/lib/vscode/node_modules/vscode-ripgrep/bin
sudo ln -sf /usr/lib/code-server/lib/vscode/node_modules/@vscode/ripgrep-universal/bin/linux-x64/rg /usr/lib/code-server/lib/vscode/node_modules/vscode-ripgrep/bin/rg
```
*Verificare:* `rg --version` returnează `ripgrep 15.0.0`.

---

### 2. Eroarea: "OpenAI completion error: 400 ... Invalid thought signature"

#### Simptom:
În timpul unei conversații în Roo Code (prin LiteLLM / OpenAI Compatible), apare eroarea:
```text
OpenAI completion error: 400 ... "Invalid thought signature.", "status": "INVALID_ARGUMENT"
```

#### Cauza Tehnică:
Modelele Gemini de generație nouă (2.5 / 3.x Flash și Pro) generează tokeni interni de gândire (*thinking*), protejați printr-o semnătură digitală (`thought_signature`). Când un apel de unealtă (*tool call*) eșuează pe server (de exemplu eroarea `ripgrep` de mai sus), clientul trimite un mesaj de eroare înapoi. Dacă adaptorul OpenAI-compatible din LiteLLM sau clientul alterează ID-ul apelului sau pierde semnătura, Google Cloud Vertex AI respinge continuarea conversației cu `Invalid thought signature`.

#### Soluții:
1. **Resetare sesiune:** Apasă butonul **`+` (New Task)** din colțul dreapta-sus al panoului Roo Code. O sesiune nouă va rula curat, iar acum când `ripgrep` funcționează, apelul de unealtă se execută cu succes fără erori.
2. **Soluția definitivă (Driver Nativ):** Treci pe driverul nativ **`Google Cloud Vertex AI`** în setările Roo Code (vezi Secțiunea 7). Driverul nativ gestionează direct protocolul Google Vertex AI fără nicio punte de translatare, eliminând complet riscul erorilor de `thought_signature`.

---

## 🛠️ Comenzi Rapide de Mentenanță

| Acțiune | Comandă |
| :--- | :--- |
| **Status code-server** | `sudo systemctl status code-server@root` |
| **Restart code-server** | `sudo systemctl restart code-server@root` |
| **Log-uri code-server** | `sudo journalctl -u code-server@root -f` |
| **Verificare porturi deschise** | `sudo firewall-cmd --zone=public --list-ports` |
| **Verificare zone firewall active** | `sudo firewall-cmd --get-active-zones` |
| **Status sincronizare Netavark** | `sudo systemctl status netavark-firewalld-reload.service` |
| **Restart stack AI complet** | `cd /opt/private-enterprise-ai-hub && ./run.sh` |
