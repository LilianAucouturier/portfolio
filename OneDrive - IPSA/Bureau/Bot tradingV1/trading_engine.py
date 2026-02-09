# -*- coding: utf-8 -*-
# trading_engine.py
import sys
import os

# Force UTF-8 for Windows immediately
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

import time
import pandas as pd
import math
import subprocess
import atexit
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

# Safe console initialization
console = Console(force_terminal=True, style=None, highlight=False)

def safe_print(text, style=None):
    """Print wrapper that handles encoding errors"""
    try:
        console.print(text, style=style)
    except Exception:
        try:
            # Fallback: remove non-ascii
            clean_text = text.encode('ascii', 'ignore').decode('ascii')
            console.print(clean_text, style=style)
        except:
            pass
from binance.client import Client
from binance.enums import *

from config import Config
from api_client import BinanceClient
from portfolio_manager import PortfolioManager
from trading_strategy import TradingStrategy
from utils import health_check, log_trade, format_quantity, calculate_position_size
from logger import setup_logging
from database import TradingDatabase
from alert_manager import AlertManager
from whatsapp_notifier import whatsapp

from optimizer import StrategyOptimizer
from strategy_simulator import StrategySimulator

# --- GESTION DU DASHBOARD (SUPPRIMÉ - GÉRÉ PAR DASHBOARD.PY) ---
# Le dashboard est maintenant le contrôleur principal

def initialize_components():
    """Initialise tous les composants du système"""
    console.print(Panel.fit("INITIALISATION DES COMPOSANTS", style="bold blue"))
    
    components = {}
    
    # Étape 1: Base de données
    console.print("🗃️  Base de données...")
    components['db'] = TradingDatabase()
    console.print("   ✅ Succès", style="green")
    
    # Étape 2: API Binance (avant PortfolioManager)
    console.print("🔗 API Binance...")
    components['api_client'] = BinanceClient()
    if not components['api_client'].test_connection():
        raise ConnectionError("Connexion Binance échouée")
    console.print("   ✅ Succès", style="green")
    
    # Étape 3: PortfolioManager (détecte les paires)
    console.print("💰 Gestionnaire de portefeuille...")
    components['portfolio_mgr'] = PortfolioManager(components['api_client'], components['db'])
    console.print("   ✅ Succès", style="green")
    
    # Étape 4: Configuration avec les paires détectées
    console.print("⚙️  Configuration...")
    components['config'] = Config()
    # 🔥 METTRE À JOUR avec toutes les paires détectées
    all_symbols = components['portfolio_mgr'].detect_available_symbols()
    components['config'].SYMBOLS_TO_SCAN = all_symbols
    console.print(f"   ✅ {len(all_symbols)} paires configurées", style="green")
    
    # Étape 5: Autres composants
    console.print("🎯 Stratégie de trading...")
    components['strategy'] = TradingStrategy()
    console.print("   ✅ Succès", style="green")
    
    console.print("🚨 Système d'alertes...")
    components['alert_manager'] = AlertManager(components['api_client'], components['db'])
    console.print("   ✅ Succès", style="green")
    
    # Test WhatsApp
    if components.get('alert_manager') and whatsapp.enabled:
        whatsapp.send_message(f"🤖 TRADE BOT\\n✅ Système démarré!\\n📊 {len(all_symbols)} paires actives")
        console.print("   ✅ Test WhatsApp réussi", style="green")

    # Étape 7: Optimiseur de stratégie
    console.print("🔧 Optimiseur de stratégie...")
    components['optimizer'] = StrategyOptimizer(components['api_client'])
    console.print("   ✅ Succès", style="green")

    # Étape 8: Simulateur de stratégies (Leaderboard)
    console.print("🎮 Simulateur de stratégies...")
    components['simulator'] = StrategySimulator(components['db'])
    console.print("   ✅ Succès", style="green")
    
    return components

def display_startup_summary(components):
    """Affiche le résumé de démarrage"""
    config = components['config']
    portfolio_mgr = components['portfolio_mgr']
    
    console.print(Panel.fit("✅ SYSTÈME DÉMARRÉ AVEC SUCCÈS !", style="bold green"))
    
    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Paramètre", style="cyan")
    summary_table.add_column("Valeur", style="white")
    
    summary_table.add_row("🎯 Paires disponibles", f"{len(config.SYMBOLS_TO_SCAN)}")
    summary_table.add_row("⏰ Intervalle scan", f"{config.SLEEP_TIME} secondes")
    summary_table.add_row("💰 Montant par trade", f"{config.EURO_AMOUNT_PER_TRADE}€")
    summary_table.add_row("📊 Stop Loss", f"{config.STOP_LOSS_PERCENT}%")
    summary_table.add_row("🎯 Take Profit", f"{config.TAKE_PROFIT_PERCENT}%")
    summary_table.add_row("🚨 Alertes WhatsApp", "✅ Activé" if whatsapp.enabled else "❌ Désactivé")
    
    console.print(summary_table)
    
    # Afficher quelques paires pour info
    if config.SYMBOLS_TO_SCAN:
        sample_pairs = config.SYMBOLS_TO_SCAN[:8]  # 8 premières
        console.print(f"📋 Paires actives: {', '.join(sample_pairs)}...", style="blue")
    
    # Positions initiales
    if portfolio_mgr.entry_prices:
        console.print(f"📊 {len(portfolio_mgr.entry_prices)} positions ouvertes:", style="green")
        for symbol, price in list(portfolio_mgr.entry_prices.items())[:5]:
            console.print(f"   • {symbol}: {price:.2f}€", style="blue")
    else:
        console.print("📊 Aucune position ouverte trouvée", style="yellow")

def execute_trading_cycle(components, cycle_number):
    """Exécute un cycle complet de trading"""
    config = components['config']
    api_client = components['api_client']
    strategy = components['strategy']
    portfolio_mgr = components['portfolio_mgr']
    db = components['db']
    alert_manager = components['alert_manager']
    
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    
    console.print(f"\n🎯 CYCLE #{cycle_number} - {current_time}", style="bold cyan")
    console.print(f"🔍 Analyse de {len(config.SYMBOLS_TO_SCAN)} paires...")
    
    # === TABLEAU PRINCIPAL ===
    table = Table(
        title=f"📊 SCAN DES PAIRES - Cycle #{cycle_number}",
        show_header=True,
        header_style="bold magenta",
        title_style="bold white"
    )
    
    # Colonnes du tableau
    table.add_column("Paire", style="cyan", width=10)
    table.add_column("Prix", style="yellow", width=12)
    table.add_column("RSI", style="blue", width=8)
    table.add_column("Tendance 4H", style="default", width=16)
    table.add_column("Signal", style="bold", width=12)
    table.add_column("Solde", style="green", width=20)
    table.add_column("P&L %", style="red", width=10)
    table.add_column("Action", style="white", width=20)
    
    # Compteurs pour le résumé
    stats = {
        'buy_signals': 0,
        'sell_signals': 0,
        'hold_signals': 0,
        'total_profit_loss': 0.0,
        'positions_count': 0,
        'trades_this_cycle': 0,
        'alerts_sent': 0
    }
    
    # === ANALYSE DE CHAQUE PAIRE ===
    for symbol in config.SYMBOLS_TO_SCAN:
        try:
            # Récupérer les données de marché
            df_5min = api_client.get_market_data(symbol, config.TIMEFRAME, config.LIMIT_CANDLES)
            if df_5min is None or df_5min.empty:
                table.add_row(symbol, "❌ Données", "N/A", "N/A", "HOLD", "N/A", "N/A", "Erreur données")
                continue
            
            # Calculer les indicateurs
            df_5min = strategy.calculate_indicators(df_5min)
            
            # Récupérer les données 4H pour la tendance
            df_4h = api_client.get_market_data(symbol, '4h', 250)
            if df_4h is None or df_4h.empty:
                table.add_row(symbol, "❌ Tendance", "N/A", "N/A", "HOLD", "N/A", "N/A", "Erreur tendance")
                continue
            
            df_4h = strategy.calculate_indicators(df_4h)
            
            # === SIMULATION STRATÉGIES PARALLÈLES (Leaderboard) ===
            try:
                # Calculer les indicateurs supplémentaires pour le simulateur
                df_sim = df_5min.copy()
                df_sim = components['simulator'].calculate_indicators(df_sim)
                components['simulator'].evaluate_strategies(symbol, df_sim)
            except Exception as e:
                console.print(f"⚠️ Erreur simulation {symbol}: {e}", style="dim")
            
            # Obtenir les données actuelles
            current_price = df_5min.iloc[-1]['close']
            current_rsi = df_5min.iloc[-1]['rsi']
            
            # Obtenir la tendance
            is_bullish, trend_text = strategy.get_trend_signal(df_4h)
            
            # Vérifier le solde
            base_asset = symbol.replace('EUR', '')
            current_balance = api_client.get_current_balance(base_asset)
            
            # Calculer la valeur de la position
            position_value = current_balance * current_price
            
            # Considérer en position seulement si la valeur est significative (> 1€)
            # Cela permet d'ignorer les "poussières" et d'autoriser l'achat même si solde > 0
            is_in_position = position_value >= 1.0
            
            # Pour la vente, on garde la même logique (doit être > 1€)
            is_sellable_position = is_in_position
            
            # Calculer le P&L si en position
            pnl_percent = 0.0
            if is_in_position and symbol in portfolio_mgr.entry_prices:
                entry_price = portfolio_mgr.entry_prices[symbol]
                if entry_price > 0:
                    pnl_percent = ((current_price - entry_price) / entry_price) * 100
                    stats['total_profit_loss'] += pnl_percent
                    stats['positions_count'] += 1
            
            # Obtenir le signal de trading
            signal = strategy.get_trading_signal(df_5min, is_sellable_position, is_bullish)
            
            # Formater l'affichage
            price_str = f"{current_price:.2f}€"
            rsi_str = f"{current_rsi:.1f}"
            
            # Couleur RSI
            if current_rsi < 30:
                rsi_str = f"[green]{current_rsi:.1f}[/green]"
            elif current_rsi > 70:
                rsi_str = f"[red]{current_rsi:.1f}[/red]"
            
            # Formater le solde
            if current_balance > 0:
                balance_value_eur = current_balance * current_price
                balance_str = f"{current_balance:.4f} ({balance_value_eur:.2f}€)"
            else:
                balance_str = "0.0000 (0.00€)"
            
            # Formater le P&L
            if pnl_percent > 0:
                pnl_str = f"[green]+{pnl_percent:.1f}%[/green]"
            elif pnl_percent < 0:
                pnl_str = f"[red]{pnl_percent:.1f}%[/red]"
            else:
                pnl_str = "0.0%"
            
            # Formater le signal avec couleurs
            if signal == 'BUY':
                signal_display = "[bold green]🟢 BUY[/bold green]"
                stats['buy_signals'] += 1
            elif signal == 'SELL' and is_sellable_position:
                signal_display = "[bold red]🔴 SELL[/bold red]"
                stats['sell_signals'] += 1
            else:
                signal_display = "[grey]⚪ HOLD[/grey]"
                stats['hold_signals'] += 1
            
            # === EXÉCUTION DES ORDRES ===
            action_taken = ""
            
            if signal == 'BUY' and not is_in_position:
                # Calculer la quantité précise
                quantity = calculate_position_size(api_client, symbol, config.EURO_AMOUNT_PER_TRADE)
                if quantity and quantity > 0:
                    if api_client.is_order_valid(symbol, quantity):
                        order = api_client.place_buy_order(symbol, quantity)
                    if order:
                        # Mettre à jour le portfolio manager
                        portfolio_mgr.entry_prices[symbol] = current_price
                        portfolio_mgr.save_entry_prices()
                        
                        # Enregistrer dans la base de données
                        log_trade(db, "ACHAT", symbol, current_price, quantity, 
                                 rsi_value=current_rsi, trend_4h=trend_text)
                        
                        # Envoyer alerte WhatsApp
                        if alert_manager:
                            alert_manager.send_trade_alert(symbol, "ACHAT", current_price, quantity)
                            stats['alerts_sent'] += 1
                        
                        action_taken = f"✅ ACHAT {quantity:.4f}"
                        stats['trades_this_cycle'] += 1
                    else:
                        action_taken = "❌ Échec achat"
            
            elif signal == 'SELL' and is_in_position:
                # Formater la quantité pour la vente
                quantity = format_quantity(symbol, current_balance, api_client)
                if quantity and quantity > 0:
                    if api_client.is_order_valid(symbol, quantity):
                        order = api_client.place_sell_order(symbol, quantity)
                        if order:
                            pnl_final = 0.0
                            if symbol in portfolio_mgr.entry_prices:
                                entry_price = portfolio_mgr.entry_prices[symbol]
                                pnl_final = ((current_price - entry_price) / entry_price) * 100
                                del portfolio_mgr.entry_prices[symbol]
                                portfolio_mgr.save_entry_prices()
                            
                            # Enregistrer dans la base de données
                            log_trade(db, "VENTE", symbol, current_price, quantity, 
                                    pnl_percent=pnl_final, reason="Signal RSI",
                                    rsi_value=current_rsi, trend_4h=trend_text)
                            
                            # Envoyer alerte WhatsApp
                            if alert_manager:
                                alert_manager.send_trade_alert(symbol, "VENTE", current_price, quantity, pnl_final)
                                stats['alerts_sent'] += 1
                            
                            action_taken = f"✅ VENTE {quantity:.4f} (P&L: {pnl_final:+.1f}%)"
                            stats['trades_this_cycle'] += 1
                        else:
                            action_taken = "❌ Échec vente"
                    else:
                        action_taken = "⏭️ Vente ignorée (<1€)"
                else:
                    action_taken = "❌ Quantité invalide"
            
            # Vérification Stop Loss et Take Profit
            elif is_in_position and symbol in portfolio_mgr.entry_prices:
                entry_price = portfolio_mgr.entry_prices[symbol]
                current_pnl = ((current_price - entry_price) / entry_price) * 100
                
                # STOP LOSS
                if current_pnl <= config.STOP_LOSS_PERCENT:
                    quantity = format_quantity(symbol, current_balance, api_client)
                    if quantity and quantity > 0:
                        order = api_client.place_sell_order(symbol, quantity)
                        if order:
                            del portfolio_mgr.entry_prices[symbol]
                            portfolio_mgr.save_entry_prices()
                            
                            log_trade(db, "STOP_LOSS", symbol, current_price, quantity,
                                     pnl_percent=current_pnl, reason="Stop Loss",
                                     rsi_value=current_rsi, trend_4h=trend_text)
                            
                            # Alerte Stop Loss
                            if alert_manager:
                                alert_manager.send_emergency_alert(
                                    f"STOP LOSS {symbol}", 
                                    f"P&L: {current_pnl:.1f}% - Prix: {current_price:.2f}€"
                                )
                                stats['alerts_sent'] += 1
                            
                            action_taken = f"🛑 STOP LOSS (P&L: {current_pnl:.1f}%)"
                            stats['trades_this_cycle'] += 1
                        else:
                            action_taken = "❌ Échec stop loss"
                    else:
                        action_taken = "⏭️ Stop Loss ignoré (<1€)"
                
                # TAKE PROFIT
                elif current_pnl >= config.TAKE_PROFIT_PERCENT:
                    quantity = format_quantity(symbol, current_balance, api_client)
                    if quantity and quantity > 0:
                        order = api_client.place_sell_order(symbol, quantity)
                        if order:
                            del portfolio_mgr.entry_prices[symbol]
                            portfolio_mgr.save_entry_prices()
                            
                            log_trade(db, "TAKE_PROFIT", symbol, current_price, quantity,
                                     pnl_percent=current_pnl, reason="Take Profit", 
                                     rsi_value=current_rsi, trend_4h=trend_text)
                            
                            # Alerte Take Profit
                            if alert_manager:
                                alert_manager.send_trade_alert(symbol, "TAKE_PROFIT", current_price, quantity, current_pnl)
                                stats['alerts_sent'] += 1
                            
                            action_taken = f"🎯 TAKE PROFIT (P&L: {current_pnl:.1f}%)"
                            stats['trades_this_cycle'] += 1
                        else:
                            action_taken = "❌ Échec take profit"
                    else:
                        action_taken = "⏭️ Take Profit ignoré (<1€)"
            
            # Ajouter la ligne au tableau
            table.add_row(
                symbol,
                price_str,
                rsi_str,
                trend_text,
                signal_display,
                balance_str,
                pnl_str,
                action_taken if action_taken else "⏳ En attente"
            )
            
        except Exception as e:
            console.print(f"❌ Erreur traitement {symbol}: {e}", style="red")
            table.add_row(symbol, "❌ Erreur", "N/A", "N/A", "HOLD", "N/A", "N/A", f"Erreur: {str(e)[:20]}...")
    
    # === AFFICHAGE DU TABLEAU ===
    console.print(table)
    return stats

def manage_portfolio_snapshot(components, stats):
    """Gère le snapshot du portefeuille"""
    config = components['config']
    api_client = components['api_client']
    portfolio_mgr = components['portfolio_mgr']
    db = components['db']
    
    try:
        # Mise à jour valeur portefeuille
        portfolio_value = portfolio_mgr.update_portfolio_value(config.SYMBOLS_TO_SCAN)
        cash_balance = api_client.get_current_balance('EUR')
        crypto_value = portfolio_value - cash_balance
        
        # Sauvegarder snapshot DB
        db.log_portfolio_snapshot(
            total_value=portfolio_value,
            cash=cash_balance,
            crypto_value=crypto_value,
            positions_count=stats['positions_count']
        )
        
        console.print(f"💾 Snapshot portefeuille: {portfolio_value:.2f}€", style="green")
        
        return portfolio_value
        
    except Exception as e:
        console.print(f"⚠️ Erreur snapshot portefeuille: {e}", style="yellow")
        return 0.0

def display_cycle_summary(cycle_number, stats, portfolio_value, total_cycles, total_trades, total_profit):
    """Affiche le résumé du cycle"""
    # Résumé du cycle
    console.print(Panel.fit(
        f"📈 RÉSUMÉ DU CYCLE #{cycle_number}\n"
        f"• Signaux ACHAT: [green]{stats['buy_signals']}[/green]\n"
        f"• Signaux VENTE: [red]{stats['sell_signals']}[/red]\n"
        f"• Signaux HOLD: [grey]{stats['hold_signals']}[/grey]\n"
        f"• Positions actives: [yellow]{stats['positions_count']}[/yellow]\n"
        f"• Trades ce cycle: [cyan]{stats['trades_this_cycle']}[/cyan]\n"
        f"• Alertes envoyées: [magenta]{stats['alerts_sent']}[/magenta]\n"
        f"• P&L moyen positions: [{'green' if stats['total_profit_loss'] >= 0 else 'red'}]{stats['total_profit_loss']/max(stats['positions_count'],1):+.1f}%[/{'green' if stats['total_profit_loss'] >= 0 else 'red'}]",
        title="📊 STATISTIQUES CYCLE",
        style="bold blue"
    ))
    
    # Statistiques globales
    total_trades += stats['trades_this_cycle']
    
    console.print(Panel.fit(
        f"🏆 STATISTIQUES GLOBALES\n"
        f"• Total cycles: [cyan]{total_cycles}[/cyan]\n"
        f"• Total trades: [green]{total_trades}[/green]\n"
        f"• Profit total: [{'green' if total_profit >= 0 else 'red'}]{total_profit:+.1f}%[/{'green' if total_profit >= 0 else 'red'}]\n"
        f"• Valeur portefeuille: [yellow]{portfolio_value:.2f}€[/yellow]",
        title="📈 PERFORMANCE GLOBALE",
        style="bold magenta"
    ))
    
    return total_trades

def check_emergency_stop(components, portfolio_value):
    """Vérifie les conditions d'arrêt d'urgence"""
    config = components['config']
    api_client = components['api_client']
    portfolio_mgr = components['portfolio_mgr']
    alert_manager = components['alert_manager']
    
    initial_investment = 1000  # À ajuster selon votre dépôt initial
    
    if portfolio_value > 0:
        drawdown = ((portfolio_value - initial_investment) / initial_investment) * 100
        
        # Affichage drawdown
        drawdown_color = "green" if drawdown >= 0 else "red"
        console.print(f"💰 Valeur portefeuille: [bold yellow]{portfolio_value:.2f}€[/bold yellow] | "
        f"Drawdown: [{drawdown_color}]{drawdown:+.1f}%[/{drawdown_color}]")
        
        # Arrêt d'urgence si drawdown trop important
        if drawdown <= config.MAX_DRAWDOWN:
            console.print(Panel.fit(
                f"🚨 ARRÊT D'URGENCE ACTIVÉ\n"
                f"Drawdown: [red]{drawdown:.1f}%[/red]\n"
                f"Limite: {config.MAX_DRAWDOWN}%\n"
                f"Fermeture de toutes les positions...",
                style="bold red"
            ))
            
            # Alerte WhatsApp urgence
            if alert_manager:
                alert_manager.send_emergency_alert(
                    "ARRÊT D'URGENCE ACTIVÉ", 
                    f"Drawdown: {drawdown:.1f}% - Fermeture positions"
                )
            
            # Fermer toutes les positions
            for symbol in list(portfolio_mgr.entry_prices.keys()):
                try:
                    base_asset = symbol.replace('EUR', '')
                    balance = api_client.get_current_balance(base_asset)
                    if balance > 0.001:
                        quantity = format_quantity(symbol, balance, api_client)
                        if quantity:
                            api_client.place_sell_order(symbol, quantity)
                            console.print(f"🔻 Fermeture position: {symbol}", style="red")
                            time.sleep(1)  # Pause entre les ordres
                except Exception as e:
                    console.print(f"❌ Erreur fermeture {symbol}: {e}", style="red")
            
            return True  # Arrêt demandé
    
    return False  # Continuer

def main():
    """Fonction principale"""
    global console
    console = Console()
    logger = setup_logging()

    # 1. Sauvegarder le PID pour le Dashboard (CORRECTION)
    try:
        pid = os.getpid()
        with open("bot.pid", "w") as f:
            f.write(str(pid))
        console.print(f"✅ PID sauvegardé: {pid}", style="dim")
    except Exception as e:
        console.print(f"⚠️ Erreur PID: {e}", style="yellow")
    
    console.print(Panel.fit("🚀 DÉMARRAGE DU SYSTÈME DE TRADING AVEC RAPPORTS QUOTIDIENS", style="bold green"))
    
    # 2. Initialiser tous les composants
    try:
        components = initialize_components()
    except Exception as e:
        console.print(f"❌ Échec initialisation: {e}", style="bold red")
        return
    
    # 3. Afficher le résumé de démarrage
    display_startup_summary(components)
    
    # 4. Attente initiale pour stabilisation
    console.print("⏳ Initialisation des données de marché (20 secondes)...", style="yellow")
    time.sleep(20)
    
    # 5. Variables de performance
    total_cycles = 0
    total_trades = 0
    total_profit = 0.0
    
    # 6. Timer pour rapports quotidiens
    last_daily_check = time.time()
    
    # 7. Boucle principale de trading
    console.print(Panel.fit("🔄 DÉMARRAGE DE LA BOUCLE DE TRADING", style="bold cyan"))
    
    # 8. Timer pour optimisation automatique
    last_optimization_check = time.time()
    last_cleanup_check = time.time()
    optimization_interval = 6 * 3600 # 6 heures en secondes

    # === NETTOYAGE DES POSITIONS INVENDABLES AU DÉMARRAGE ===
    console.print("🧹 Vérification des positions invendables...", style="yellow")
    cleaned_count = components['portfolio_mgr'].cleanup_unsellable_positions(
    components['api_client'], 
    components['config'].SYMBOLS_TO_SCAN)
    if cleaned_count > 0:
        console.print(f"🧹 {cleaned_count} positions invendables nettoyées", style="yellow")
    else:
        console.print("✅ Aucune position invendable trouvée", style="green")

    while True:
        try:
            total_cycles += 1
            current_time = time.time()
            
            # === OPTIMISATION AUTOMATIQUE (toutes les 6 heures) ===
            if current_time - last_optimization_check > optimization_interval:
                console.print("🔧 Vérification optimisation automatique...", style="blue")
                
                # Lancer optimisation seulement si peu de trades récents
                recent_trades = components['db'].get_trade_history(limit=10)
                if len(recent_trades) < 5:  # Peu d'activité récente
                    symbols_to_optimize = components['config'].SYMBOLS_TO_SCAN[:20]  # 20 premières paires
                    components['optimizer'].auto_optimize_strategy(symbols_to_optimize)
                
                last_optimization_check = current_time

            # === NETTOYAGE PÉRIODIQUE DES POSITIONS INVENDABLES (toutes les 24h) ===
            if current_time - last_cleanup_check > 24 * 3600:  # 24 heures
                console.print("🧹 Nettoyage périodique des positions invendables...", style="yellow")
                cleaned_count = components['portfolio_mgr'].cleanup_unsellable_positions(
                    components['api_client'], 
                    components['config'].SYMBOLS_TO_SCAN)
                if cleaned_count > 0:
                    console.print(f"🧹 {cleaned_count} positions invendables nettoyées", style="yellow")
                last_cleanup_check = current_time

            # === GESTION DES RAPPORTS QUOTIDIENS ===
            if components['alert_manager']:
                # Vérifier toutes les minutes si c'est 21h pour le rapport
                if current_time - last_daily_check > 60:  # Vérifier toutes les minutes
                    performance_stats = components['db'].get_performance_stats(days=1)
                    components['alert_manager'].send_daily_report(performance_stats)
                    last_daily_check = current_time
            
            # === RECHARGEMENT CONFIGURATION ===
            try:
                # Recharge silencieusement la config en cas de changement via le dashboard
                components['config'].load_dynamic_config(silent=True)
            except Exception as e:
                pass

            # === CYCLE DE TRADING PRINCIPAL ===

            stats = execute_trading_cycle(components, total_cycles)
            
            # === GESTION PORTEFEUILLE ===
            portfolio_value = manage_portfolio_snapshot(components, stats)
            
            # === RÉSUMÉ ET STATISTIQUES ===
            total_trades = display_cycle_summary(
                total_cycles, stats, portfolio_value, 
                total_cycles, total_trades, total_profit
            )
            
            # === VÉRIFICATION ARRÊT URGENCE ===
            if check_emergency_stop(components, portfolio_value):
                break
            
            # === VÉRIFICATION ARRÊT GRACIEUX (POUR WHATSAPP) ===
            if os.path.exists(".stop_signal"):
                console.print(Panel.fit("🛑 ARRÊT DEMANDÉ PAR L'UTILISATEUR", style="bold yellow"))
                break

            # === PROCHAIN CYCLE ===
            console.print(Panel.fit(
                f"⏰ Prochain scan dans {components['config'].SLEEP_TIME} secondes...\n"
                f"🕒 {time.strftime('%H:%M:%S')} → {time.strftime('%H:%M:%S', time.localtime(time.time() + components['config'].SLEEP_TIME))}",
                style="bold cyan"
            ))
            
            # Attente avant le prochain cycle
            sleep_time = components['config'].SLEEP_TIME
            for remaining in range(sleep_time, 0, -1):
                # Vérification rapide pendant l'attente
                if os.path.exists(".stop_signal"):
                    console.print(Panel.fit("🛑 ARRÊT DEMANDÉ PAR L'UTILISATEUR", style="bold yellow"))
                    raise KeyboardInterrupt # Sortir via l'exception pour propre nettoyage

                if remaining % 60 == 0 or remaining == 30:  # Afficher toutes les minutes et à 30s
                    console.print(f"⏳ Prochain cycle dans {remaining}s...", style="dim")
                time.sleep(1)
            
        except KeyboardInterrupt:
            console.print(Panel.fit("🛑 ARRÊT MANUEL DEMANDÉ", style="bold yellow"))
            break
            
        except Exception as e:
            logger.error(f"Erreur critique dans la boucle principale: {e}")
            console.print(Panel.fit(
                f"❌ ERREUR CRITIQUE\n{str(e)}\n"
                f"Redémarrage dans 60 secondes...",
                style="bold red"
            ))
            
            # Alerte WhatsApp erreur critique
            if components.get('alert_manager'):
                components['alert_manager'].send_emergency_alert(
                    "ERREUR CRITIQUE BOT", 
                    f"Redémarrage automatique - {str(e)[:100]}"
                )
            
            time.sleep(60)

    # === NETTOYAGE FINAL ===
    console.print(Panel.fit("🧹 FERMETURE PROPRE DU SYSTÈME", style="bold green"))
    
    # Fermer la base de données
    try:
        if 'db' in locals():
            components['db'].close()
        console.print("✅ Base de données fermée", style="green")
    except Exception as e:
        console.print(f"⚠️ Erreur fermeture DB: {e}", style="yellow")
    
    # Nettoyer fichier signal
    if os.path.exists(".stop_signal"):
        try:
            os.remove(".stop_signal")
        except:
            pass
    
    # Alerte arrêt
    if components.get('alert_manager'):
        components['alert_manager'].send_message(
            f"🤖 TRADE BOT\\n"
            f"🛑 Système arrêté\\n"
            f"📊 {total_cycles} cycles exécutés\\n"
            f"🎯 {total_trades} trades effectués"
        )
    console.print(Panel.fit(
        f"🎯 STATISTIQUES FINALES\n"
        f"• Cycles exécutés: {total_cycles}\n"
        f"• Trades totaux: {total_trades}\n"
        f"• Profit total: {total_profit:+.1f}%\n"
        f"• Positions restantes: {len(components['portfolio_mgr'].entry_prices)}",
        style="bold blue"
    ))
    
    console.print("✅ Bot arrêté avec succès!", style="bold green")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        console.print(Panel.fit(
            f"❌ ERREUR FATALE\n"
            f"{traceback.format_exc()}",
            style="bold red"
        ))
        print("\n🛑 Le programme s'est arrêté à cause d'une erreur.")
        input("⌨️  Appuyez sur Entrée pour fermer la fenêtre...")