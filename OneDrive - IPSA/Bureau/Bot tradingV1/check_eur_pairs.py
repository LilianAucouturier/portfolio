import os
from binance.client import Client
from rich.console import Console
from dotenv import load_dotenv

def detect_available_eur_pairs():
    """Détecte et retourne les paires EUR disponibles sur le testnet"""
    console = Console()
    
    # 🔧 CORRECTION : Charger les variables d'environnement
    load_dotenv()
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    # 🔧 CORRECTION : Créer le client Binance (manquant dans votre code)
    client = Client(api_key, api_secret, testnet=True)
    
    desired_pairs = [
        'BTCEUR', 'ETHEUR', 'BNBEUR', 'SOLEUR', 'XRPEUR', 
        'AVAXEUR', 'DOTEUR', 'ATOMEUR', 'TRXEUR','LINKEUR', 
        'LTCEUR', 'XLMEUR'
    ]
    
    available_pairs = []
        
    for pair in desired_pairs:
        try:
            # Tester si la paire existe
            client.get_symbol_ticker(symbol=pair)
            available_pairs.append(pair)
        except: 
            continue 
    
    console.print(f"🎯 {len(available_pairs)} paires EUR disponibles sur {len(desired_pairs)}")
    return available_pairs

# Si le fichier est exécuté directement
if __name__ == "__main__":
    pairs = detect_available_eur_pairs()
    print(f"\n📋 Liste pour config.py: {pairs}")