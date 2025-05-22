import cloudscraper
import json
import time
import requests
from datetime import datetime
import os

print("🚀 Extracteur Vinted → Discord Webhook (Achats uniquement)")
print("=" * 65)

def load_config():
    """Charge la configuration depuis config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("❌ Fichier config.json non trouvé!")
        print("💡 Copiez config.example.json vers config.json et configurez vos tokens")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erreur dans config.json: {str(e)}")
        return None

def create_working_scraper(config):
    """Crée un scraper qui contourne Cloudflare"""
    print("🔧 Création du scraper CloudScraper...")
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Authorization': f'Bearer {config["vinted"]["access_token"]}',
            'Content-Type': 'application/json',
            'Referer': 'https://www.vinted.fr/',
            'Origin': 'https://www.vinted.fr'
        }
        
        scraper.headers.update(headers)
        
        print("✅ Scraper CloudScraper créé avec succès")
        return scraper
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du scraper: {str(e)}")
        return None

def test_connection(scraper):
    """Test la connexion à l'API Vinted"""
    print("\n🔐 Test de connexion...")
    
    try:
        response = scraper.get('https://www.vinted.fr/api/v2/users/current', timeout=15)
        
        if response.status_code == 200 and response.text.strip():
            user_data = response.json()
            user = user_data.get('user', {})
            username = user.get('login', 'Utilisateur inconnu')
            user_id = user.get('id', 'ID inconnu')
            print(f"✅ Connecté en tant que: {username} (ID: {user_id})")
            return True, username
        else:
            print(f"❌ Échec de la connexion (Status: {response.status_code})")
            return False, None
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        return False, None

def is_order_completed(status):
    """Détermine si une commande est terminée/finalisée"""
    if not status:
        return False
    
    status_lower = status.lower()
    
    completed_statuses = [
        'completed', 'delivered', 'finished', 'closed', 'cancelled', 'refunded',
        'dispute_closed', 'rated', 'transaction_completed', 'livré', 'terminé',
        'évaluation donnée', 'tout va bien', 'échange effectué', 'commande livrée'
    ]
    
    for completed_status in completed_statuses:
        if completed_status in status_lower:
            return True
    
    return False

def get_active_purchases(scraper):
    """Récupère uniquement les achats en cours"""
    print("\n🛒 Récupération des achats en cours...")
    
    purchases = []
    page = 1
    per_page = 20
    
    while True:
        try:
            url = f"https://www.vinted.fr/api/v2/my_orders?type=purchased&status=in_progress&per_page={per_page}&page={page}"
            print(f"   📄 Page {page}: Chargement...")
            
            response = scraper.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get('my_orders', [])
                
                if not orders:
                    print(f"   🏁 Aucun achat en cours sur cette page")
                    break
                
                # Filtrer les commandes actives
                for order in orders:
                    if not is_order_completed(order.get('status', '')):
                        purchases.append(order)
                        print(f"   ✅ Achat actif: {order.get('title', 'N/A')[:40]} | {order.get('status', 'N/A')}")
                
                if len(orders) < per_page:
                    break
                
                page += 1
                time.sleep(1)
                
            else:
                print(f"   ❌ Erreur {response.status_code}")
                break
                
        except Exception as e:
            print(f"   ❌ Erreur lors de la récupération: {str(e)}")
            break
    
    print(f"   📊 Total achats en cours: {len(purchases)}")
    return purchases

def get_transaction_details(scraper, transaction_id):
    """Récupère les détails complets d'une transaction"""
    try:
        url = f"https://www.vinted.fr/api/v2/transactions/{transaction_id}"
        response = scraper.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def extract_purchase_info(scraper, order):
    """Extrait toutes les informations d'un achat pour Discord"""
    print(f"   🔍 Analyse: {order.get('title', 'N/A')[:30]}...")
    
    # Informations de base
    purchase_info = {
        'title': order.get('title', 'Article sans titre'),
        'price': order.get('price', {}).get('amount', 'N/A'),
        'currency': order.get('price', {}).get('currency_code', 'EUR'),
        'status': order.get('status', 'Statut inconnu'),
        'date': order.get('date', 'Date inconnue'),
        'transaction_id': order.get('transaction_id', 'N/A'),
        'conversation_id': order.get('conversation_id', 'N/A'),
        'tracking_number': None,
        'carrier': None,
        'shipping_status': None,
        'image_url': None,
        'vinted_url': None,
        'seller_info': None
    }
    
    # Extraire l'image de l'annonce
    if 'photo' in order and order['photo']:
        photo = order['photo']
        # Priorité aux images de qualité
        if 'url' in photo:
            purchase_info['image_url'] = photo['url']
        elif 'thumbnails' in photo and photo['thumbnails']:
            # Prendre la plus grande miniature disponible
            largest_thumb = max(photo['thumbnails'], key=lambda x: x.get('width', 0) * x.get('height', 0))
            purchase_info['image_url'] = largest_thumb['url']
    
    # Construire l'URL Vinted (estimation basée sur l'ID de transaction)
    if purchase_info['transaction_id'] != 'N/A':
        purchase_info['vinted_url'] = f"https://www.vinted.fr/member/purchases/orders"
    
    # Récupérer les détails de la transaction
    detail_data = get_transaction_details(scraper, purchase_info['transaction_id'])
    
    if detail_data and 'transaction' in detail_data:
        transaction = detail_data['transaction']
        
        # Extraire les infos de shipping
        if 'shipment' in transaction and transaction['shipment']:
            shipment = transaction['shipment']
            
            # Numéro de tracking
            if 'tracking_code' in shipment:
                purchase_info['tracking_number'] = str(shipment['tracking_code'])
            
            # Transporteur
            if 'carrier' in shipment and shipment['carrier']:
                carrier = shipment['carrier']
                purchase_info['carrier'] = carrier.get('name', 'Transporteur inconnu')
            
            # Statut de livraison
            if 'status_title' in shipment:
                purchase_info['shipping_status'] = shipment['status_title']
        
        # Informations du vendeur
        if 'seller' in transaction and transaction['seller']:
            seller = transaction['seller']
            purchase_info['seller_info'] = {
                'username': seller.get('login', 'Vendeur inconnu'),
                'rating': seller.get('positive_feedback_count', 0)
            }
    
    if purchase_info['tracking_number']:
        print(f"      ✅ Tracking trouvé: {purchase_info['tracking_number']} ({purchase_info['carrier']})")
    else:
        print(f"      ❌ Pas de tracking")
    
    return purchase_info

def format_purchase_for_discord(purchase, index, config):
    """Formate les informations d'un achat pour Discord"""
    
    # Déterminer la couleur de l'embed selon le statut
    color_map = {
        'bordereau envoyé': config['discord']['color_scheme']['info'],       # Bleu
        'expédié': config['discord']['color_scheme']['success'],             # Vert
        'en transit': config['discord']['color_scheme']['success'],          # Vert
        'livré': config['discord']['color_scheme']['success'],               # Vert
        'paiement validé': config['discord']['color_scheme']['warning'],     # Orange
        'en attente': config['discord']['color_scheme']['error']             # Rouge
    }
    
    status_lower = purchase['status'].lower()
    embed_color = 0x9b59b6  # Violet par défaut
    
    for status_key, color in color_map.items():
        if status_key in status_lower:
            embed_color = color
            break
    
    # Construire l'embed
    embed = {
        "title": f"📦 {purchase['title']}",
        "color": embed_color,
        "timestamp": datetime.now().isoformat(),
        "fields": [
            {
                "name": "💰 Prix",
                "value": f"{purchase['price']} {purchase['currency']}",
                "inline": True
            },
            {
                "name": "📊 Statut",
                "value": purchase['status'],
                "inline": True
            }
        ],
        "footer": {
            "text": f"Achat #{index} • Transaction: {purchase['transaction_id']}"
        }
    }
    
    # Ajouter l'image si disponible et si activé dans la config
    if config['features']['include_images'] and purchase['image_url']:
        embed["thumbnail"] = {"url": purchase['image_url']}
    
    # Ajouter les informations de tracking
    if purchase['tracking_number']:
        embed["fields"].append({
            "name": "🚚 Numéro de suivi",
            "value": f"`{purchase['tracking_number']}`",
            "inline": False
        })
        
        if purchase['carrier']:
            embed["fields"].append({
                "name": "🏢 Transporteur",
                "value": purchase['carrier'],
                "inline": True
            })
    else:
        embed["fields"].append({
            "name": "🚚 Suivi",
            "value": "❌ Pas encore de numéro de tracking",
            "inline": False
        })
    
    # Ajouter les informations du vendeur si activé
    if config['features']['include_seller_info'] and purchase['seller_info']:
        seller = purchase['seller_info']
        embed["fields"].append({
            "name": "👤 Vendeur",
            "value": f"{seller['username']} ({seller['rating']} évaluations positives)",
            "inline": True
        })
    
    # Ajouter la date
    if purchase['date'] and purchase['date'] != 'Date inconnue':
        try:
            # Convertir la date ISO en format lisible
            date_obj = datetime.fromisoformat(purchase['date'].replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%d/%m/%Y à %H:%M')
            embed["fields"].append({
                "name": "📅 Date d'achat",
                "value": formatted_date,
                "inline": True
            })
        except:
            pass
    
    return embed

def send_to_discord(purchases, username, config):
    """Envoie les achats sur Discord via webhook"""
    print(f"\n📤 Envoi vers Discord webhook...")
    
    webhook_url = config['discord']['webhook_url']
    
    if not webhook_url or webhook_url == "VOTRE_WEBHOOK_DISCORD_ICI":
        print("❌ Webhook Discord non configuré!")
        print("💡 Ajoutez votre webhook dans config.json → discord → webhook_url")
        return False
    
    try:
        # Message principal (si activé)
        if config['features']['send_summary']:
            main_message = {
                "username": config['discord']['username'],
                "avatar_url": config['discord']['avatar_url'],
                "embeds": [
                    {
                        "title": "🛒 Rapport des achats Vinted en cours",
                        "description": f"**Utilisateur:** {username}\n**Achats actifs trouvés:** {len(purchases)}\n**Dernière mise à jour:** {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}",
                        "color": config['discord']['color_scheme']['success'],
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
            
            # Envoyer le message principal
            response = requests.post(webhook_url, json=main_message)
            
            if response.status_code not in [200, 204]:
                print(f"❌ Erreur envoi message principal: {response.status_code}")
                return False
            
            print("✅ Message principal envoyé")
            time.sleep(config['tracking']['rate_limit_delay'])
        
        # Envoyer chaque achat individuellement
        for i, purchase in enumerate(purchases, 1):
            embed = format_purchase_for_discord(purchase, i, config)
            
            message = {
                "username": config['discord']['username'],
                "avatar_url": config['discord']['avatar_url'],
                "embeds": [embed]
            }
            
            response = requests.post(webhook_url, json=message)
            
            if response.status_code in [200, 204]:
                print(f"   ✅ Achat #{i} envoyé: {purchase['title'][:30]}...")
            else:
                print(f"   ❌ Erreur achat #{i}: {response.status_code}")
            
            time.sleep(config['tracking']['rate_limit_delay'])
        
        # Message de résumé final (si activé)
        if config['features']['send_summary']:
            tracking_count = len([p for p in purchases if p['tracking_number']])
            summary_message = {
                "username": config['discord']['username'],
                "avatar_url": config['discord']['avatar_url'],
                "embeds": [
                    {
                        "title": "📊 Résumé",
                        "description": f"**✅ Avec tracking:** {tracking_count}/{len(purchases)}\n**❌ Sans tracking:** {len(purchases) - tracking_count}\n**📈 Taux de suivi:** {(tracking_count/len(purchases)*100):.1f}%",
                        "color": config['discord']['color_scheme']['info'],
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=summary_message)
            
            if response.status_code in [200, 204]:
                print("✅ Résumé final envoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi Discord: {str(e)}")
        return False

def main():
    print("🎯 Démarrage de l'extraction Vinted → Discord\n")
    
    # Charger la configuration
    config = load_config()
    if not config:
        return
    
    # Vérifier la configuration du webhook
    webhook_url = config['discord']['webhook_url']
    if not webhook_url or webhook_url == "VOTRE_WEBHOOK_DISCORD_ICI":
        print("⚠️  ATTENTION: Webhook Discord non configuré!")
        print("📝 Modifiez config.json → discord → webhook_url avec votre webhook Discord")
        print("🔗 Pour créer un webhook: Paramètres du serveur → Intégrations → Webhooks → Nouveau webhook")
        print("\n" + "="*60 + "\n")
    
    # Créer le scraper
    scraper = create_working_scraper(config)
    if not scraper:
        print("❌ Impossible de créer le scraper")
        return
    
    # Tester la connexion
    connected, username = test_connection(scraper)
    if not connected:
        print("❌ Impossible de se connecter à l'API Vinted")
        return
    
    # Récupérer les achats en cours
    purchases_raw = get_active_purchases(scraper)
    
    if not purchases_raw:
        print("❌ Aucun achat en cours trouvé")
        return
    
    print(f"\n🔍 Extraction des détails pour {len(purchases_raw)} achats...")
    
    # Extraire les détails complets
    purchases_detailed = []
    for i, purchase in enumerate(purchases_raw, 1):
        detailed_info = extract_purchase_info(scraper, purchase)
        purchases_detailed.append(detailed_info)
        time.sleep(config['tracking']['rate_limit_delay'])
    
    # Sauvegarder localement si activé
    if config['features']['save_local_backup']:
        if not os.path.exists('discord_results'):
            os.makedirs('discord_results')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(f"discord_results/purchases_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(purchases_detailed, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Données sauvegardées localement")
    
    # Envoyer sur Discord
    discord_success = send_to_discord(purchases_detailed, username, config)
    
    # Résumé final
    tracking_count = len([p for p in purchases_detailed if p['tracking_number']])
    
    print(f"\n🎉 EXTRACTION TERMINÉE!")
    print("=" * 40)
    print(f"🛒 Achats en cours: {len(purchases_detailed)}")
    print(f"🚚 Avec tracking: {tracking_count}")
    print(f"❌ Sans tracking: {len(purchases_detailed) - tracking_count}")
    print(f"📤 Discord: {'✅ Envoyé' if discord_success else '❌ Échec'}")
    
    if not discord_success:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"\n💡 Les données sont sauvegardées dans discord_results/purchases_{timestamp}.json")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Extraction interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Programme terminé")