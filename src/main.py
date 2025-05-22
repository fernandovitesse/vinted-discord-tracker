"""
Vinted Discord Tracker - Point d'entrée principal
Automatisation du suivi des achats Vinted avec notifications Discord
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from src.vinted_api import VintedAPI
from src.discord_webhook import DiscordWebhook
from src.tracking_extractor import TrackingExtractor
from src.utils import setup_logging, load_config

def main():
    """Point d'entrée principal de l'application"""
    
    print("🚀 Vinted Discord Tracker - Démarrage")
    print("=" * 50)
    
    try:
        # 1. Chargement de la configuration
        print("📋 Chargement de la configuration...")
        config = load_config()
        
        # 2. Configuration du logging
        print("📝 Configuration du logging...")
        logger = setup_logging(config.get('logging', {}))
        logger.info("Application démarrée")
        
        # 3. Validation de la configuration
        print("✅ Validation de la configuration...")
        if not validate_config(config):
            print("❌ Configuration invalide. Vérifiez config.json")
            return 1
        
        # 4. Initialisation des services
        print("🔧 Initialisation des services...")
        
        # API Vinted
        vinted_api = VintedAPI(
            access_token=config['vinted']['access_token'],
            config=config['vinted']
        )
        
        # Webhook Discord
        discord_webhook = DiscordWebhook(
            webhook_url=config['discord']['webhook_url'],
            config=config['discord']
        )
        
        # Extracteur de tracking
        tracker = TrackingExtractor(
            vinted_api=vinted_api,
            discord_webhook=discord_webhook,
            config=config['tracking']
        )
        
        # 5. Test de connexion
        print("🔐 Test de connexion Vinted...")
        if not vinted_api.test_connection():
            print("❌ Impossible de se connecter à Vinted")
            return 1
        
        print("📤 Test du webhook Discord...")
        if not discord_webhook.test_webhook():
            print("❌ Impossible de joindre le webhook Discord")
            return 1
        
        # 6. Exécution principale
        print("🎯 Début de l'extraction des achats...")
        result = tracker.extract_and_send()
        
        # 7. Résumé final
        if result['success']:
            print(f"\n🎉 EXTRACTION RÉUSSIE!")
            print(f"📦 Achats traités: {result['total_purchases']}")
            print(f"🚚 Avec tracking: {result['with_tracking']}")
            print(f"📤 Messages Discord envoyés: {result['messages_sent']}")
            logger.info(f"Extraction réussie: {result['total_purchases']} achats traités")
            return 0
        else:
            print(f"\n❌ ERREUR LORS DE L'EXTRACTION")
            print(f"Détails: {result.get('error', 'Erreur inconnue')}")
            logger.error(f"Extraction échouée: {result.get('error')}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Extraction interrompue par l'utilisateur")
        return 0
        
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {str(e)}")
        if 'logger' in locals():
            logger.exception("Erreur inattendue")
        return 1

def validate_config(config):
    """Valide la configuration"""
    
    required_keys = [
        ('vinted', 'access_token'),
        ('discord', 'webhook_url')
    ]
    
    for section, key in required_keys:
        if section not in config:
            print(f"❌ Section manquante: {section}")
            return False
        if key not in config[section]:
            print(f"❌ Clé manquante: {section}.{key}")
            return False
        if not config[section][key] or config[section][key] == f"VOTRE_{key.upper()}_ICI":
            print(f"❌ {section}.{key} non configuré")
            return False
    
    return True

def show_help():
    """Affiche l'aide"""
    
    help_text = """
🛒 Vinted Discord Tracker - Aide

UTILISATION:
    python src/main.py [options]

OPTIONS:
    -h, --help          Afficher cette aide
    -v, --version       Afficher la version
    -c, --config FILE   Utiliser un fichier de config spécifique
    --test              Mode test (n'envoie pas sur Discord)
    --dry-run          Afficher les données sans les envoyer

EXEMPLES:
    python src/main.py                          # Exécution normale
    python src/main.py --test                   # Mode test
    python src/main.py -c config_test.json     # Config spécifique
    
CONFIGURATION:
    1. Copiez config.example.json vers config.json
    2. Remplissez vos tokens Vinted et webhook Discord
    3. Lancez le script
    
SUPPORT:
    - GitHub: https://github.com/fernandovitesse/vinted-discord-tracker
    - Issues: https://github.com/fernandovitesse/vinted-discord-tracker/issues
    """
    
    print(help_text)

if __name__ == "__main__":
    # Gestion des arguments de ligne de commande
    args = sys.argv[1:]
    
    if "-h" in args or "--help" in args:
        show_help()
        sys.exit(0)
        
    if "-v" in args or "--version" in args:
        print("Vinted Discord Tracker v1.0.0")
        sys.exit(0)
    
    # Exécution principale
    exit_code = main()
    sys.exit(exit_code)