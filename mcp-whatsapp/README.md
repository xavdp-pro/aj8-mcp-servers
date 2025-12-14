# MCP WhatsApp Server (Baileys)

Serveur MCP pour WhatsApp utilisant Baileys (API WhatsApp Web non officielle).

## Fonctionnalités

- ✅ Envoi/réception de messages texte
- ✅ Envoi/réception d'images, vidéos, documents
- ✅ **Récupération des messages vocaux** (PTT) → fichiers `.ogg`
- ✅ Envoi de notes vocales
- ✅ Liste des groupes
- ✅ Webhooks pour messages entrants en temps réel

## Architecture

```
mcp-whatsapp/
├── server.py           # MCP Server (Python)
├── baileys/
│   ├── index.js        # Bridge Node.js Baileys
│   └── package.json
├── auth/               # Session WhatsApp (auto-généré)
├── downloads/          # Médias téléchargés (vocaux, images...)
└── README.md
```

## Installation

### 1. Installer les dépendances Node.js (Baileys)

```bash
cd mcp-whatsapp/baileys
npm install
```

### 2. Installer les dépendances Python (MCP Server)

```bash
cd mcp-whatsapp
pip install -r requirements.txt
```

## Démarrage

### Étape 1 : Lancer le bridge Baileys

```bash
cd mcp-whatsapp/baileys
node index.js
```

Un **QR code** s'affichera dans le terminal. Scannez-le avec WhatsApp.

### Étape 2 : Le MCP Server se connecte automatiquement

Le MCP Server (`server.py`) communique avec Baileys via l'API REST sur le port 3033.

## Outils MCP disponibles

| Outil | Description |
|-------|-------------|
| `whatsapp_status` | Statut de connexion + QR code si en attente |
| `whatsapp_send_message` | Envoyer un message texte |
| `whatsapp_send_media` | Envoyer image/vidéo/document |
| `whatsapp_send_voice` | Envoyer une note vocale (PTT) |
| `whatsapp_list_chats` | Lister les groupes |
| `whatsapp_list_downloads` | Lister les médias téléchargés |
| `whatsapp_get_voice_notes` | Récupérer les vocaux (.ogg) pour transcription |
| `whatsapp_register_webhook` | Enregistrer un webhook pour messages entrants |

## Variables d'environnement

| Variable | Default | Description |
|----------|---------|-------------|
| `BAILEYS_PORT` | 3033 | Port API REST Baileys |
| `BAILEYS_URL` | http://localhost:3033 | URL pour le MCP Server |

## Limitations

- ⚠️ API non officielle (risque de ban si usage abusif)
- ⚠️ Nécessite de rescanner le QR si déconnecté trop longtemps
- ⚠️ Un seul compte WhatsApp par instance
