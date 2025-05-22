# 🛒 Vinted Discord Tracker

> **Automatisation du suivi de vos achats Vinted avec notifications Discord**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Discord](https://img.shields.io/badge/Discord-Webhook-7289da.svg)](https://discord.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎯 Fonctionnalités

- ✅ **Extraction automatique** des achats Vinted en cours
- 🚚 **Tracking des numéros de suivi** (Mondial Relay, Chronopost, Vinted Go)
- 📤 **Notifications Discord** avec embeds riches et images
- 🔄 **Monitoring en temps réel** des changements de statut
- 📊 **Interface utilisateur** claire et informative
- 🛡️ **Sécurité** avec gestion des tokens et rate limiting

## 🚀 Installation rapide

```bash
git clone https://github.com/fernandovitesse/vinted-discord-tracker.git
cd vinted-discord-tracker
pip install -r requirements.txt
cp config.example.json config.json
# Configurez vos tokens dans config.json
python src/vinted_tracker.py
```

## ⚙️ Configuration

1. **Récupérer vos tokens Vinted** :
   - Connectez-vous à Vinted.fr
   - Ouvrez les outils de développement (F12)
   - Onglet Network → Recherchez les requêtes API
   - Copiez `access_token` depuis les headers Authorization

2. **Créer un webhook Discord** :
   - Paramètres du serveur → Intégrations → Webhooks
   - Nouveau webhook → Copier l'URL

3. **Configurer le bot** :
   ```json
   {
     "vinted": {
       "access_token": "VOTRE_TOKEN_VINTED"
     },
     "discord": {
       "webhook_url": "VOTRE_WEBHOOK_DISCORD"
     }
   }
   ```

## 📊 Exemple de sortie Discord

```
🛒 Rapport des achats Vinted en cours
Utilisateur: votre_username
Achats actifs trouvés: 5

📦 iPhone 13
💰 Prix: 350.00 EUR
📊 Statut: Bordereau envoyé au vendeur
🚚 Numéro de suivi: 22266796
🏢 Transporteur: Mondial Relay
👤 Vendeur: seller123 (45 évaluations positives)
```

## 🛠️ Utilisation

### Exécution simple
```bash
python src/main.py
```

### Exécution programmée (recommandé)
Ajoutez à votre crontab pour vérifier toutes les heures :
```bash
0 * * * * cd /path/to/vinted-discord-tracker && python src/main.py
```

## 📋 Roadmap

- [ ] 🔔 Notifications de changement de statut
- [ ] 📍 Intégration API transporteurs (suivi détaillé)
- [ ] 🤖 Exécution automatique programmée
- [ ] 📱 Bot Discord interactif avec commandes
- [ ] 📊 Dashboard web pour visualisation
- [ ] 🔄 Support multi-comptes Vinted

## 🤝 Contribution

Les contributions sont les bienvenues ! 

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit vos changements (`git commit -m 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

## 📜 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## ⚠️ Avertissement

Ce bot utilise l'API non-officielle de Vinted. Utilisez-le de manière responsable et respectez les conditions d'utilisation de Vinted.

## 🙏 Remerciements

- **Vinted** pour leur plateforme
- **Discord** pour les webhooks
- **CloudScraper** pour contourner Cloudflare

---

**⭐ Si ce projet vous aide, n'hésitez pas à lui donner une étoile !**
