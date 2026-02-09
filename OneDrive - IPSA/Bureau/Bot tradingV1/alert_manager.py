# alert_manager.py - VERSION AVEC RAPPORTS QUOTIDIENS À 21H
import time
import pandas as pd
import numpy as np
from rich.console import Console
from database import TradingDatabase
from whatsapp_notifier import whatsapp
from config import Config

console = Console()

class AlertManager:
    def __init__(self, api_client, db):
        self.api_client = api_client
        self.db = db
        self.last_alerts = {}
        self.alert_cooldown = {
            'TRADE': 60,      # 1 minute entre alertes trade
            'SIGNAL': 300,    # 5 minutes entre alertes signal
            'EMERGENCY': 300  # 5 minutes entre alertes urgence
        }
        self.last_daily_report_sent = None
    
    def can_send_alert(self, alert_type, symbol=None):
        """Vérifie le cooldown des alertes"""
        key = f"{alert_type}_{symbol}" if symbol else alert_type
        now = time.time()
        
        if key in self.last_alerts:
            elapsed = now - self.last_alerts[key]
            if elapsed < self.alert_cooldown.get(alert_type, 300):
                return False
        
        self.last_alerts[key] = now
        return True
    
    def safe_data_conversion(self, df, column):
        """Conversion sécurisée des données"""
        try:
            if df is None or df.empty or column not in df.columns:
                return None
            return pd.to_numeric(df[column], errors='coerce')
        except Exception as e:
            console.print(f"❌ Erreur conversion {column}: {e}", style="red")
            return None
    
    def calculate_rsi_safe(self, df, period=14):
        """Calcule le RSI de manière sécurisée"""
        try:
            if df is None or len(df) < period:
                return 50.0
            
            # Utiliser la stratégie existante si disponible
            if hasattr(df, 'rsi') and not df.empty:
                return df['rsi'].iloc[-1] if 'rsi' in df.columns and not pd.isna(df['rsi'].iloc[-1]) else 50.0
            
            # Fallback: calcul manuel
            close_prices = self.safe_data_conversion(df, 'close')
            if close_prices is None:
                return 50.0
            
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50.0
            
        except Exception as e:
            console.print(f"❌ Erreur calcul RSI: {e}", style="red")
            return 50.0
    
    def get_trend_direction_safe(self, df):
        """Détermine la direction de la tendance de manière sécurisée"""
        try:
            if df is None or len(df) < 20:
                return "NEUTRE"
            
            # Utiliser la tendance calculée si disponible
            if hasattr(df, 'ma50') and 'ma50' in df.columns and not df.empty:
                current_price = self.safe_data_conversion(df, 'close')
                ma50 = self.safe_data_conversion(df, 'ma50')
                
                if current_price is not None and ma50 is not None:
                    last_price = current_price.iloc[-1] if not current_price.empty else 0
                    last_ma50 = ma50.iloc[-1] if not ma50.empty else 0
                    
                    if not pd.isna(last_price) and not pd.isna(last_ma50):
                        return "HAUSSIER" if last_price > last_ma50 else "BAISSIER"
            
            # Fallback: calcul simple
            close_prices = self.safe_data_conversion(df, 'close')
            if close_prices is None:
                return "NEUTRE"
            
            ma_fast = close_prices.rolling(9).mean()
            ma_slow = close_prices.rolling(21).mean()
            
            if pd.isna(ma_fast.iloc[-1]) or pd.isna(ma_slow.iloc[-1]):
                return "NEUTRE"
            
            return "HAUSSIER" if ma_fast.iloc[-1] > ma_slow.iloc[-1] else "BAISSIER"
                
        except Exception as e:
            console.print(f"❌ Erreur tendance: {e}", style="red")
            return "NEUTRE"
    
    def check_market_conditions(self, symbols):
        """Surveillance marché DÉSACTIVÉE - Ne rien faire"""
        # Cette méthode est maintenant vide pour désactiver les alertes marché
        console.print("🔇 Alertes marché désactivées", style="dim")
        return 0
    
    def monitor_portfolio_health(self, portfolio_value, initial_investment=1000):
        """Surveillance portfolio DÉSACTIVÉE - Ne rien faire"""
        # Cette méthode est maintenant vide pour désactiver les alertes portfolio
        console.print("🔇 Alertes portfolio désactivées", style="dim")
        return
    
    def should_send_daily_report(self):
        """Vérifie si on doit envoyer le rapport quotidien à 21h"""
        try:
            now = time.localtime()
            current_hour = now.tm_hour
            current_minute = now.tm_min
            
            # Vérifier si c'est 21h (9 PM)
            if current_hour == 21 and current_minute == 0:
                today = time.strftime('%Y-%m-%d')
                
                # Vérifier qu'on n'a pas déjà envoyé le rapport aujourd'hui
                if self.last_daily_report_sent != today:
                    self.last_daily_report_sent = today
                    return True
            
            return False
            
        except Exception as e:
            console.print(f"❌ Erreur vérification heure rapport: {e}", style="red")
            return False
    
    def send_daily_report(self, performance_stats):
        """Rapport quotidien à 21h - VERSION AMÉLIORÉE"""
        try:
            if not self.should_send_daily_report():
                return
                
            console.print("📊 Envoi du rapport quotidien à 21h...", style="green")
            
            # Stats du jour
            daily_stats = self.db.get_performance_stats(days=1)
            
            # Message clair et concis
            message = "📊 RAPPORT QUOTIDIEN\n"
            message += "═" * 30 + "\n"
            message += f"📈 Trades du jour: {daily_stats.get('total_trades', 0)}\n"
            message += f"🎯 Win Rate: {daily_stats.get('win_rate', 0):.1f}%\n"
            message += f"💰 P&L Jour: {daily_stats.get('total_pnl_eur', 0):+.2f}€\n"
            message += f"📊 Positions actives: {len(self.load_entry_prices())}\n"
            
            # Performance notable
            if daily_stats.get('total_pnl_eur', 0) > 0:
                message += "🚀 Journée positive !\n"
            elif daily_stats.get('total_pnl_eur', 0) < 0:
                message += "📉 Journée négative\n"
            else:
                message += "⚖️  Journée neutre\n"
                
            message += "═" * 30
            
            # Envoyer le rapport
            success = whatsapp.send_message(f"🤖 TRADE BOT\n{message}")
            if success:
                console.print("✅ Rapport quotidien envoyé", style="green")
            
        except Exception as e:
            console.print(f"❌ Erreur rapport quotidien: {e}", style="red")
    
    def load_entry_prices(self):
        """Charge les prix d'entrée depuis la DB"""
        try:
            trades_df = self.db.get_trade_history(limit=1000)
            open_positions = {}
            
            for symbol in Config().SYMBOLS_TO_SCAN:
                symbol_trades = trades_df[trades_df['symbol'] == symbol]
                buys = symbol_trades[symbol_trades['action'].str.contains('ACHAT|BUY', case=False, na=False)]
                sells = symbol_trades[symbol_trades['action'].str.contains('VENTE|SELL|STOP_LOSS|TAKE_PROFIT', case=False, na=False)]
                
                if len(buys) > len(sells) and not buys.empty:
                    last_buy = buys.iloc[0]
                    open_positions[symbol] = last_buy['entry_price']
            
            return open_positions
            
        except Exception as e:
            console.print(f"❌ Erreur chargement positions: {e}", style="red")
            return {}
    
    def send_trade_alert(self, symbol, action, price, quantity, pnl=None):
        """Alertes de trading - MESSAGES SIMPLIFIÉS"""
        try:
            if not whatsapp.enabled:
                return False
                
            # Messages plus courts et clairs
            if action.upper() in ['ACHAT', 'BUY']:
                message = f"🟢 ACHAT {symbol}"
                message += f" | Prix: {price:.2f}€"
                message += f" | Quantité: {quantity:.2f}"
            else:
                message = f"🔴 VENTE {symbol}"
                message += f" | Prix: {price:.2f}€" 
                message += f" | Quantité: {quantity:.2f}"
                if pnl is not None:
                    message += f" | P&L: {pnl:+.1f}%"
            
            return whatsapp.send_message(f"🤖 TRADE BOT\n{message}", "HIGH")
            
        except Exception as e:
            console.print(f"❌ Erreur alerte trade: {e}", style="red")
            return False
    
    def send_emergency_alert(self, issue, details):
        """Alertes d'urgence - ACTIVÉES (seulement pour arrêts d'urgence)"""
        try:
            if not whatsapp.enabled:
                return False
                
            message = f"🚨 URGENCE: {issue}"
            message += f"\n🔍 Détails: {details}"
            message += f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            return whatsapp.send_message(f"🤖 TRADE BOT\\n{message}", "URGENT")
            
        except Exception as e:
            console.print(f"❌ Erreur alerte urgence: {e}", style="red")
            return False

    def send_message(self, message):
        """Envoie un message générique via WhatsApp"""
        try:
            return whatsapp.send_message(message)
        except Exception as e:
            console.print(f"❌ Erreur envoi message générique: {e}", style="red")
            return False