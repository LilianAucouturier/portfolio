import math
import time
import logging
import os
from rich.console import Console
from config import Config

console = Console()
logger = logging.getLogger(__name__)

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
            raise Exception("Impossible de trouver LOT_SIZE")

        precision = int(round(-math.log10(step_size)))
        factor = 10 ** precision
        formatted_quantity = math.floor(quantity * factor) / factor
        
        console.print(f"🔧 Formatage {symbol}: {quantity} → {formatted_quantity}", style="blue")
        return formatted_quantity
        
    except Exception as e:
        console.print(f"❌ Erreur formatage quantité {symbol}: {e}", style="red")
        return None

def calculate_position_size(api_client, symbol, euro_amount):
    """Calcule la taille de position précise"""
    try:
        ticker = api_client.safe_api_call(api_client.client.get_symbol_ticker, symbol=symbol)
        if not ticker:
            return None
            
        current_price = float(ticker['price'])
        quantity = euro_amount / current_price
        
        # Formatage selon les règles Binance
        formatted_quantity = format_quantity(symbol, quantity, api_client)
        return formatted_quantity
        
    except Exception as e:
        console.print(f"❌ Erreur calcul position {symbol}: {e}", style="red")
        return None

def log_trade(db, action, symbol, prix, quantity=0, pnl_percent=None, 
              pnl_eur=0, reason="", rsi_value=None, trend_4h=None):
    """Journalise les trades dans la base de données"""
    try:
        entry_price = prix if action.upper() in ['ACHAT', 'BUY'] else None
        exit_price = prix if action.upper() in ['VENTE', 'SELL', 'STOP_LOSS', 'TAKE_PROFIT'] else None
        
        success = db.log_trade(
            symbol=symbol,
            action=action.upper(),
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            pnl_percent=pnl_percent,
            pnl_eur=pnl_eur,
            reason=reason,
            strategy_version="v2.0",
            rsi_value=rsi_value,
            trend_4h=trend_4h
        )
        
        # Backup dans l'ancien fichier texte
        if success:
            try:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                log_line = f"[{timestamp}] - {action.upper()} - {symbol} @ {prix:.2f} EUR"
                
                if pnl_percent is not None:
                    log_line += f" - P&L: {pnl_percent:+.2f}%\n"
                else:
                    log_line += "\n"
                    
                os.makedirs('data', exist_ok=True)
                with open(Config.TRADE_LOG_FILE, "a") as f:
                    f.write(log_line)
            except:
                pass
        
        return success
        
    except Exception as e:
        console.print(f"❌ Erreur journal trade DB: {e}", style="red")
        return False

def health_check(api_client):
    """Vérifie la santé du système"""
    try:
        # Test connexion API
        account = api_client.safe_api_call(api_client.client.get_account)
        if not account:
            return False
        
        # Vérifie solde EUR
        euro_balance = api_client.get_current_balance('EUR')
        required_min = Config.EURO_AMOUNT_PER_TRADE * 3
        
        if euro_balance < required_min:
            console.print(f"⚠️ ATTENTION: Solde EUR faible: {euro_balance:.2f} EUR", style="yellow")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Échec health check: {e}", style="red")
        return False