# api_client.py - VERSION AVEC FILTRE MINIMUM 1€
import pandas as pd
import math
from binance.client import Client
from binance.enums import *
from config import Config
from rich.console import Console

console = Console()

class BinanceClient:
    def __init__(self):
        self.client = Client(Config.API_KEY, Config.API_SECRET, testnet=Config.TESTNET)
    
    def safe_api_call(self, func, *args, **kwargs):
        """Wrapper pour gérer les erreurs API"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            console.print(f"Erreur API {func.__name__}: {e}", style="red")
            return None
    
    def safe_data_conversion(self, df, columns):
        """Conversion sécurisée des colonnes DataFrame"""
        try:
            if df is None or df.empty:
                return df
                
            for col in columns:
                if col in df.columns:
                    # Remplacer les chaînes problématiques avant conversion
                    df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        except Exception as e:
            console.print(f"❌ Erreur conversion données: {e}", style="red")
            return df
    
    def is_order_valid(self, symbol, quantity, current_price=None):
        """Vérifie si l'ordre respecte le minimum de 1€"""
        try:
            current_price = self.get_current_price(symbol)
            if not current_price:
                return False
                
            order_value = quantity * current_price
            
            if order_value < 1.0:
                console.print(f"⏭️ Ordre ignoré {symbol}: {order_value:.2f}€ < 1€ minimum", style="yellow")
                return False
                
            return True
            
        except Exception as e:
            console.print(f"❌ Erreur validation ordre {symbol}: {e}", style="red")
            return False
    
    def get_market_data(self, symbol, timeframe, limit):
        """Récupère les données de marché et les convertit en DataFrame - VERSION CORRIGÉE"""
        klines = self.safe_api_call(
            self.client.get_klines,
            symbol=symbol,
            interval=timeframe, 
            limit=limit
        )
        
        if klines:
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Conversion sécurisée de toutes les colonnes numériques
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                              'quote_asset_volume', 'number_of_trades',
                              'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
            df = self.safe_data_conversion(df, numeric_columns)
            
            return df
        return None
    
    def get_current_balance(self, asset):
        """Récupère le solde d'un actif"""
        balance = self.safe_api_call(self.client.get_asset_balance, asset=asset)
        if balance:
            return float(balance['free'])
        return 0.0
    
    def get_symbol_info(self, symbol):
        """Récupère les informations d'un symbole (filters, précisions, etc.)"""
        return self.safe_api_call(self.client.get_symbol_info, symbol=symbol)
    
    def get_current_price(self, symbol):
        """Récupère le prix actuel d'un symbole"""
        ticker = self.safe_api_call(self.client.get_symbol_ticker, symbol=symbol)
        if ticker:
            return float(ticker['price'])
        return None
    
    def place_buy_order(self, symbol, quantity):
        """Place un ordre d'achat market AVEC FILTRE 1€"""
        try:
            # ✅ VÉRIFICATION MINIMUM 1€
            if not self.is_order_valid(symbol, quantity):
                return None
                
            order = self.safe_api_call(
                self.client.order_market_buy,
                symbol=symbol,
                quantity=quantity
            )
            if order:
                current_price = self.get_current_price(symbol)
                order_value = quantity * current_price
                console.print(f"✅ ORDRE D'ACHAT réussi: {quantity} {symbol} ({order_value:.2f}€)", style="green")
            return order
        except Exception as e:
            console.print(f"❌ Erreur ordre d'achat {symbol}: {e}", style="red")
            return None
    
    def place_sell_order(self, symbol, quantity):
        """Place un ordre de vente market AVEC FILTRE 1€"""
        try:
            # ✅ VÉRIFICATION MINIMUM 1€
            if not self.is_order_valid(symbol, quantity):
                return None
                
            order = self.safe_api_call(
                self.client.order_market_sell,
                symbol=symbol,
                quantity=quantity
            )
            if order:
                current_price = self.get_current_price(symbol)
                order_value = quantity * current_price
                console.print(f"✅ ORDRE DE VENTE réussi: {quantity} {symbol} ({order_value:.2f}€)", style="green")
            return order
        except Exception as e:
            console.print(f"❌ Erreur ordre de vente {symbol}: {e}", style="red")
            return None
    
    def place_buy_order_quote(self, symbol, quote_amount):
        """Place un ordre d'achat avec un montant en quote (EUR)"""
        try:
            # ✅ VÉRIFICATION MINIMUM 1€
            if quote_amount < 1.0:
                console.print(f"⏭️ Achat ignoré {symbol}: {quote_amount:.2f}€ < 1€ minimum", style="yellow")
                return None
                
            order = self.safe_api_call(
                self.client.order_market_buy,
                symbol=symbol,
                quoteOrderQty=quote_amount
            )
            if order:
                console.print(f"✅ ORDRE D'ACHAT réussi: {quote_amount}€ de {symbol}", style="green")
            return order
        except Exception as e:
            console.print(f"❌ Erreur ordre d'achat {symbol}: {e}", style="red")
            return None
    
    def get_account_info(self):
        """Récupère les informations du compte"""
        return self.safe_api_call(self.client.get_account)
    
    def get_open_orders(self, symbol=None):
        """Récupère les ordres ouverts"""
        return self.safe_api_call(self.client.get_open_orders, symbol=symbol)
    
    def cancel_order(self, symbol, order_id):
        """Annule un ordre"""
        return self.safe_api_call(self.client.cancel_order, symbol=symbol, orderId=order_id)
    
    def get_order_status(self, symbol, order_id):
        """Récupère le statut d'un ordre"""
        return self.safe_api_call(self.client.get_order, symbol=symbol, orderId=order_id)
    
    def get_server_time(self):
        """Récupère l'heure du serveur Binance"""
        return self.safe_api_call(self.client.get_server_time)
    
    def test_connection(self):
        """Teste la connexion à l'API"""
        try:
            server_time = self.get_server_time()
            if server_time:
                console.print("✅ Connexion API Binance réussie", style="green")
                return True
            else:
                console.print("❌ Connexion API Binance échouée", style="red")
                return False
        except Exception as e:
            console.print(f"❌ Test connexion échoué: {e}", style="red")
            return False

# Fonction utilitaire pour formater les quantités
def format_quantity(symbol, quantity, api_client):
    """Formate la quantité selon les règles Binance"""
    try:
        info = api_client.get_symbol_info(symbol)
        if not info:
            return None
            
        step_size = 0.0
        for f in info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                break
        
        if step_size == 0.0:
            raise Exception("Impossible de trouver le filtre LOT_SIZE")

        precision = int(round(-math.log10(step_size)))
        factor = 10 ** precision
        formatted_quantity = math.floor(quantity * factor) / factor
        
        console.print(f"🔧 Formatage {symbol}: {quantity} → {formatted_quantity}", style="blue")
        return formatted_quantity
        
    except Exception as e:
        console.print(f"❌ Erreur formatage quantité {symbol}: {e}", style="red")
        return None

# Fonction pour calculer la taille de position
def calculate_position_size(api_client, symbol, euro_amount):
    """Calcule la taille de position précise"""
    try:
        current_price = api_client.get_current_price(symbol)
        if not current_price:
            return None
            
        # Calcul de la quantité brute
        quantity = euro_amount / current_price
        
        # Formatage selon les règles Binance
        formatted_quantity = format_quantity(symbol, quantity, api_client)
        return formatted_quantity
        
    except Exception as e:
        console.print(f"❌ Erreur calcul position {symbol}: {e}", style="red")
        return None