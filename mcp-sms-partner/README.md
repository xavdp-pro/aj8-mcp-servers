# MCP SMS Partner Server

Serveur MCP pour envoyer des SMS via l'API SMS Partner (service français).

## Configuration

Ajouter la clé API dans votre fichier `.env` :

```bash
SMS_PARTNER_API_KEY=votre_cle_api
```

## Outils MCP disponibles

| Outil | Description |
|-------|-------------|
| `sms_send` | Envoyer un SMS à un numéro |
| `sms_send_bulk` | Envoyer un SMS à plusieurs numéros |
| `sms_credits` | Vérifier le solde de crédits |
| `sms_status` | Statut d'un SMS envoyé |
| `sms_history` | Historique des SMS envoyés |
| `sms_stop_list` | Liste des numéros STOP |
| `sms_add_stop` | Ajouter un numéro en STOP |

## Exemples d'utilisation

### Envoyer un SMS
```json
{
  "phone": "33612345678",
  "message": "Bonjour, ceci est un test",
  "sender": "AJ8"
}
```

### Envoyer à plusieurs numéros
```json
{
  "phones": ["33612345678", "33698765432"],
  "message": "Message groupé",
  "sender": "AJ8"
}
```

## Tarifs SMS Partner

- France : ~0.045€/SMS
- International : variable selon pays
- Crédits prépayés

## Documentation API

- Site : https://www.smspartner.fr/
- API Doc : https://docpartner.dev/
