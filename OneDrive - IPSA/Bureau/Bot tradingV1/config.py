# config.py - VERSION COMPLÈTE AVEC WHATSAPP
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Binance
    API_KEY = os.getenv('BINANCE_API_KEY')
    API_SECRET = os.getenv('BINANCE_API_SECRET')
    TESTNET = True
    
    # WhatsApp CallMeBot Configuration
    WHATSAPP_API_KEY = os.getenv('WHATSAPP_API_KEY')  # Clé CallMeBot
    WHATSAPP_PHONE = os.getenv('WHATSAPP_PHONE')      # Votre numéro avec indicatif
    
    # Intervalles d'alertes (secondes)
    ALERT_INTERVALS = {
        'MARKET_SCAN': 900,      # 15 minutes
        'PORTFOLIO_CHECK': 1800, # 30 minutes  
        'DAILY_REPORT': 86400,   # 24 heures
        'HEALTH_CHECK': 3600,    # 1 heure
    }
    
    # Seuils d'alertes
    ALERT_THRESHOLDS = {
        'RSI_OVERSOLD': 25,
        'RSI_OVERBOUGHT': 75,
        'CRITICAL_DRAWDOWN': -15,
        'WARNING_DRAWDOWN': -10,
        'VOLUME_SPIKE': 1.5,  # Multiplicateur volume
    }
    
    # Paramètres de trading
    STOP_LOSS_PERCENT = -5.0
    TAKE_PROFIT_PERCENT = 10.0
    EURO_AMOUNT_PER_TRADE = 15.0
    MAX_DRAWDOWN = -20.0
    MAX_POSITIONS = 10
    
    # Fichiers
    ENTRY_PRICE_FILE = "data/entry_prices.json"
    LOG_FILE = "data/trading_bot.log"
    TRADE_LOG_FILE = "data/journal_de_bord.txt"
    
    # Base de données
    DB_PATH = "data/trading.db"
    
    # ⚡ PAIRES AUTOMATIQUES - Initialisé dans __init__
    SYMBOLS_TO_SCAN = []
    
    # Paramètres techniques
    TIMEFRAME = '5m'
    LIMIT_CANDLES = 1000
    SLEEP_TIME = 300  # 5 minutes entre les cycles de trading
    
    # Timeframes pour analyse multi-échelle
    TIMEFRAMES_MULTI = {
        'SHORT_TERM': '5m',   # Court terme - signaux
        'MEDIUM_TERM': '1h',  # Moyen terme - tendance
        'LONG_TERM': '4h',    # Long terme - contexte
    }
    
    # Paramètres indicateurs techniques
    INDICATOR_SETTINGS = {
        'RSI_PERIOD': 14,
        'BB_PERIOD': 20,
        'BB_STD': 2,
        'MA_SHORT': 20,
        'MA_MEDIUM': 50,
        'MA_LONG': 200,
        'MACD_FAST': 12,
        'MACD_SLOW': 26,
        'MACD_SIGNAL': 9,
    }
    
    # Stratégie - Seuils de confluence
    STRATEGY_THRESHOLDS = {
        'MIN_BUY_SIGNALS': 0.6,  # 60% des conditions d'achat
        'MIN_SELL_SIGNALS': 0.6, # 60% des conditions de vente
        'RSI_OVERSOLD': 30,
        'RSI_OVERBOUGHT': 70,
        'TREND_CONFIRMATION': 0.5, # 50% signaux haussiers
    }
    
    # Cooldowns (secondes)
    COOLDOWNS = {
        'TRADE_ALERT': 60,      # 1 minute entre alertes trade
        'SIGNAL_ALERT': 300,    # 5 minutes entre alertes signal
        'PORTFOLIO_ALERT': 3600, # 1 heure entre alertes portfolio
        'EMERGENCY_ALERT': 300, # 5 minutes entre alertes urgence
    }
    
    def __init__(self):
        self.SYMBOLS_TO_SCAN = []      
        os.makedirs('data', exist_ok=True)
        self.check_whatsapp_config()
        self.load_dynamic_config()

    def load_dynamic_config(self, silent=False):
        """Charge la configuration dynamique depuis JSON"""
        import json
        try:
            if os.path.exists("data/config.json"):
                with open("data/config.json", "r") as f:
                    data = json.load(f)
                    # Mettre à jour les attributs de classe
                    for key, value in data.items():
                        if hasattr(Config, key):
                            setattr(Config, key, value)
                    if not silent:
                        print("✅ Configuration dynamique chargée")
        except Exception as e:
            print(f"⚠️ Erreur chargement config: {e}")

    @classmethod
    def save_dynamic_config(cls, new_config):
        """Sauvegarde la configuration dynamique"""
        import json
        try:
            # Charger l'existant pour ne pas écraser
            current_config = {}
            if os.path.exists("data/config.json"):
                with open("data/config.json", "r") as f:
                    current_config = json.load(f)
            
            # Mettre à jour
            current_config.update(new_config)
            
            with open("data/config.json", "w") as f:
                json.dump(current_config, f, indent=4)
            return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde config: {e}")
            return False

    def update_symbols_list(self, symbols):
        """Met à jour la liste des symboles avec ceux détectés par PortfolioManager"""
        self.SYMBOLS_TO_SCAN = symbols
        print(f"🎯 {len(self.SYMBOLS_TO_SCAN)} paires disponibles pour le trading")
    
    def check_whatsapp_config(self):
        """Vérifie et log la configuration WhatsApp"""
        from rich.console import Console
        console = Console()
        
        if self.WHATSAPP_API_KEY and self.WHATSAPP_PHONE:
            console.print("✅ Configuration WhatsApp détectée", style="green")
        else:
            console.print("⚠️  Configuration WhatsApp manquante", style="yellow")
    
    @classmethod
    def get_current_time(cls):
        """Retourne l'heure actuelle formatée"""
        import time
        return time.strftime('%Y-%m-%d %H:%M:%S')
    
    @classmethod
    def validate_config(cls):
        """Valide la configuration complète"""
        errors = []
        
        # Vérification clés API Binance
        if not cls.API_KEY:
            errors.append("BINANCE_API_KEY manquante dans .env")
        if not cls.API_SECRET:
            errors.append("BINANCE_API_SECRET manquante dans .env")
        
        # Vérification montants trading
        if cls.EURO_AMOUNT_PER_TRADE <= 0:
            errors.append("EURO_AMOUNT_PER_TRADE doit être > 0")
        if cls.STOP_LOSS_PERCENT >= 0:
            errors.append("STOP_LOSS_PERCENT doit être négatif")
        if cls.TAKE_PROFIT_PERCENT <= 0:
            errors.append("TAKE_PROFIT_PERCENT doit être positif")
        
        # Vérification intervalles
        if cls.SLEEP_TIME < 60:
            errors.append("SLEEP_TIME doit être >= 60 secondes")
        
        return errors
    
    @classmethod
    def get_alert_emoji(cls, alert_type):
        """Retourne l'emoji approprié pour le type d'alerte"""
        emojis = {
            'BUY': '🟢',
            'SELL': '🔴', 
            'HOLD': '⚪',
            'OVERSOLD': '📈',
            'OVERBOUGHT': '📉',
            'BREAKOUT': '🎯',
            'EMERGENCY': '🚨',
            'PORTFOLIO': '💰',
            'HEALTH': '🏥',
            'INFO': 'ℹ️'
        }
        return emojis.get(alert_type, '📢')
    
    @classmethod
    def get_timeframe_display_name(cls, timeframe):
        """Retourne le nom d'affichage pour un timeframe"""
        display_names = {
            '5m': '5 Minutes',
            '1h': '1 Heure', 
            '4h': '4 Heures',
            '1d': '1 Jour',
            '1w': '1 Semaine'
        }
        return display_names.get(timeframe, timeframe)
    
    @classmethod 
    def get_strategy_description(cls):
        """Retourne la description de la stratégie"""
        return {
            'name': 'Stratégie Multi-Échelles RSI + Tendance',
            'version': '2.0',
            'description': 'Combinaison RSI court terme avec tendance 4H et analyse volume',
            'timeframes': cls.TIMEFRAMES_MULTI,
            'indicators': list(cls.INDICATOR_SETTINGS.keys())
        }

# Validation au chargement
if __name__ == "__main__":
    config_errors = Config.validate_config()
    if config_errors:
        print("❌ ERREURS DE CONFIGURATION:")
        for error in config_errors:
            print(f"   • {error}")
    else:
        print("✅ Configuration valide")
        
    # Test d'initialisation
    try:
        config = Config()
        print(f"✅ {len(config.SYMBOLS_TO_SCAN)} paires détectées")
        print(f"📊 Stratégie: {config.get_strategy_description()['name']}")
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")