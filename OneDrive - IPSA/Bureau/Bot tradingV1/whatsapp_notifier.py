# whatsapp_notifier.py
import requests
import json
from rich.console import Console
from config import Config
import logging
import urllib.parse

console = Console()
logger = logging.getLogger(__name__)

class WhatsAppNotifier:
    def __init__(self):
        self.callmebot_api_key = Config.WHATSAPP_API_KEY
        self.phone_number = Config.WHATSAPP_PHONE
        self.enabled = bool(self.callmebot_api_key and self.phone_number)
    
    def send_message(self, message, priority="MEDIUM"):
        """Envoie un message WhatsApp via CallMeBot API"""
        if not self.enabled:
            console.print(f"📱 WhatsApp désactivé: {message}", style="yellow")
            return False
        
        try:
            # Nettoyer le message pour URL
            clean_message = urllib.parse.quote(message)
            
            url = f"https://api.callmebot.com/whatsapp.php?phone={self.phone_number}&text={clean_message}&apikey={self.callmebot_api_key}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200 or response.status_code == 210:
                console.print(f"✅ WhatsApp envoyé: {message}", style="green")
                return True
            else:
                console.print(f"❌ Erreur WhatsApp {response.status_code}: {message}", style="red")
                return False
                
        except Exception as e:
            console.print(f"❌ Erreur envoi WhatsApp: {e}", style="red")
            return False
    
    def send_trade_alert(self, symbol, action, price, quantity, pnl=None):
        """Alertes de trading"""
        emoji = "🟢" if action.upper() in ['ACHAT', 'BUY'] else "🔴"
        message = f"{emoji} {action.upper()} {symbol}"
        message += f"\n💶 Prix: {price:.2f}€"
        message += f"\n📊 Quantité: {quantity:.4f}"
        
        if pnl is not None:
            pnl_emoji = "📈" if pnl > 0 else "📉"
            message += f"\n{pnl_emoji} P&L: {pnl:+.2f}%"
        
        return self.send_message(f"🤖 TRADE BOT\\n{message}", "HIGH")
    
    def send_signal_alert(self, symbol, signal, price, rsi, trend):
        """Alertes de signaux"""
        emoji = "🎯" if signal == 'BUY' else "⚠️" if signal == 'SELL' else "ℹ️"
        message = f"{emoji} SIGNAL {signal} {symbol}"
        message += f"\n💶 Prix: {price:.2f}€"
        message += f"\n📊 RSI: {rsi:.1f}"
        message += f"\n📈 Tendance: {trend}"
        
        return self.send_message(f"🤖 TRADE BOT\\n{message}", "MEDIUM")
    
    def send_portfolio_alert(self, total_value, pnl_total, positions_count):
        """Alertes portfolio"""
        pnl_emoji = "🚀" if pnl_total > 0 else "🔻" if pnl_total < 0 else "⚖️"
        message = f"{pnl_emoji} SNAPSHOT PORTEFEUILLE"
        message += f"\n💰 Valeur: {total_value:.2f}€"
        message += f"\n📈 P&L Total: {pnl_total:+.2f}%"
        message += f"\n📊 Positions: {positions_count}"
        
        return self.send_message(f"🤖 TRADE BOT\\n{message}", "LOW")
    
    def send_emergency_alert(self, issue, details):
        """Alertes d'urgence"""
        message = f"🚨 URGENCE: {issue}"
        message += f"\n🔍 Détails: {details}"
        message += f"\n⏰ {Config.get_current_time()}"
        
        return self.send_message(f"🤖 TRADE BOT\\n{message}", "URGENT")

# Instance globale
whatsapp = WhatsAppNotifier()