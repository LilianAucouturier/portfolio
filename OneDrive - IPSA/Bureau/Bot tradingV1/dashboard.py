# dashboard.py - VERSION COMPLÈTE AVEC ISOLATION STREAMLIT
import os
import sys

# ISOLATION COMPLÈTE POUR STREAMLIT - AU TRÈS DÉBUT
if __name__ == "__main__":
    # Désactiver complètement Rich pour Streamlit
    os.environ["RICHLIVE"] = "false"
    os.environ["TERM"] = "dumb"  # Mode simple pour terminal
    
    # Rediriger stdout/stderr pour éviter les conflits
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

# Force UTF-8 encoding for Windows (fixes UnicodeEncodeError)
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Maintenant les imports normaux
import streamlit as st
import pandas as pd
import ta
from binance.client import Client
from binance.enums import *
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- IMPORT BASE DE DONNÉES ---
from database import TradingDatabase
from config import Config
from sentiment_analyzer import SentimentAnalyzer

# --- CONFIGURATION SÉCURISÉE ---
st.set_page_config(
    page_title="🤖 Bot Trading Dashboard Pro", 
    layout="wide",
    page_icon="🚀"
)

# --- CHARGEMENT DES VARIABLES D'ENVIRONNEMENT ---
load_dotenv()

# --- FONCTION PRINT SÉCURISÉE POUR WINDOWS ---
def safe_print(message):
    """Print sécurisé pour éviter les erreurs d'encodage Windows"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Enlève les émojis et caractères problématiques
        clean_message = message.encode('ascii', 'ignore').decode('ascii')
        print(clean_message)

# --- IMPORT DES CONFIGURATIONS ---
# Clés API depuis .env
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# Liste des paires depuis check_eur_pairs
try:
    from check_eur_pairs import detect_available_eur_pairs
    SYMBOLS = detect_available_eur_pairs()
    safe_print(f"OK - {len(SYMBOLS)} paires chargees depuis check_eur_pairs")
except Exception as e:
    safe_print(f"ERREUR chargement paires: {e}")
    # Liste de secours
    SYMBOLS = [
        'BTCEUR', 'ETHEUR', 'BNBEUR', 'SOLEUR', 'XRPEUR', 
        'ADAEUR', 'AVAXEUR', 'DOTEUR', 'TRXEUR',
        'DOGEEUR', 'SHIBEUR', 'LINKEUR',
        'LTCEUR', 'BCHEUR', 'XLMEUR'
    ]

# --- CONNEXION BINANCE SÉCURISÉE ---
@st.cache_resource
def init_client():
    if not API_KEY or not API_SECRET:
        st.error("ERREUR: Cles API manquantes dans le fichier .env")
        return None
    try:
        client = Client(API_KEY, API_SECRET, testnet=True)
        # Test de connexion
        client.get_account()
        st.sidebar.success("✅ Connecté à Binance")
        return client
    except Exception as e:
        st.error(f"ERREUR connexion Binance: {e}")
        return None

client = init_client()

# --- FONCTIONS BASE DE DONNÉES ---
def load_portfolio_history():
    """Charge l'historique du portefeuille depuis la DB"""
    try:
        db = TradingDatabase()
        history_df = db.get_portfolio_history(days=30)
        
        # Convertir en format compatible avec l'existant
        portfolio_history = {}
        for _, row in history_df.iterrows():
            portfolio_history[row['timestamp']] = row['total_value']
            
        safe_print(f"OK - Historique DB chargé: {len(portfolio_history)} points")
        return portfolio_history
        
    except Exception as e:
        safe_print(f"ERREUR chargement historique DB: {e}")
        # Fallback sur l'ancien système
        try:
            with open("data/portfolio_history.json", "r") as f:
                data = json.load(f)
                safe_print(f"OK - Historique JSON de secours: {len(data)} points")
                return data
        except:
            return {}

def load_entry_prices():
    """Charge les prix d'entrée depuis la DB"""
    try:
        db = TradingDatabase()
        trades_df = db.get_trade_history(limit=1000)
        
        entry_prices = {}
        for symbol in SYMBOLS:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            buys = symbol_trades[symbol_trades['action'].str.contains('ACHAT|BUY', case=False, na=False)]
            sells = symbol_trades[symbol_trades['action'].str.contains('VENTE|SELL|STOP_LOSS|TAKE_PROFIT', case=False, na=False)]
            
            # Si plus d'achats que de ventes, position ouverte
            if len(buys) > len(sells) and not buys.empty:
                entry_prices[symbol] = buys.iloc[0]['entry_price']
                
        safe_print(f"OK - Entry prices DB chargés: {len(entry_prices)} positions")
        return entry_prices
        
    except Exception as e:
        safe_print(f"ERREUR chargement entry prices DB: {e}")
        # Fallback sur l'ancien système
        try:
            with open("data/entry_prices.json", "r") as f:
                return json.load(f)
        except:
            return {}

def update_portfolio_history():
    """Met à jour l'historique du portefeuille - AVEC DB"""
    try:
        portfolio_history = load_portfolio_history()
        current_value = get_portfolio_value()
        
        # Éviter de sauvegarder si changement < 0.1€ (réduit le bruit)
        if portfolio_history:
            last_value = list(portfolio_history.values())[-1]
            if abs(current_value - last_value) < 0.1:
                return portfolio_history
        
        # Ajouter le nouveau point dans la DB
        db = TradingDatabase()
        
        # Calculer les composants du portefeuille
        cash_balance = 0.0
        crypto_value = 0.0
        positions_count = 0
        
        if client:
            try:
                # Solde EUR
                cash_balance = float(client.get_asset_balance(asset='EUR')['free'])
                
                # Cryptos
                entries = load_entry_prices()
                positions_count = len(entries)
                
                for symbol in SYMBOLS:
                    base_asset = symbol.replace('EUR', '')
                    try:
                        balance = float(client.get_asset_balance(asset=base_asset)['free'])
                        if balance > 0:
                            ticker = client.get_symbol_ticker(symbol=symbol)
                            price = float(ticker['price'])
                            crypto_value += balance * price
                    except:
                        continue
            except:
                pass
        
        # Sauvegarder dans la DB
        db.log_portfolio_snapshot(
            total_value=current_value,
            cash=cash_balance,
            crypto_value=crypto_value,
            positions_count=positions_count
        )
        
        # Mettre à jour le dictionnaire local pour l'affichage immédiat
        current_time = datetime.now().isoformat()
        portfolio_history[current_time] = current_value
        
        safe_print(f"OK - Snapshot DB sauvegardé: {current_value:.2f}€")
        return portfolio_history
        
    except Exception as e:
        safe_print(f"ERREUR mise à jour historique DB: {e}")
        return {}

def get_performance_stats_from_db():
    """Récupère les statistiques de performance depuis la DB"""
    try:
        db = TradingDatabase()
        stats = db.get_performance_stats(days=30)
        return stats
    except Exception as e:
        safe_print(f"ERREUR stats performance DB: {e}")
        return {}

def get_strategy_analysis_from_db():
    """Récupère l'analyse de stratégie depuis la DB"""
    try:
        db = TradingDatabase()
        analysis = db.get_strategy_analysis()
        return analysis
    except Exception as e:
        safe_print(f"ERREUR analyse stratégie DB: {e}")
        return {}

def get_trade_history_from_db(limit=50):
    """Récupère l'historique des trades depuis la DB"""
    try:
        db = TradingDatabase()
        trades_df = db.get_trade_history(limit=limit)
        return trades_df
    except Exception as e:
        safe_print(f"ERREUR historique trades DB: {e}")
        return pd.DataFrame()

def get_leaderboard_from_db():
    """Récupère le classement des stratégies"""
    try:
        db = TradingDatabase()
        leaderboard = db.get_strategy_leaderboard()
        return leaderboard
    except Exception as e:
        safe_print(f"ERREUR leaderboard DB: {e}")
        return []

def get_portfolio_value():
    """Calcule la valeur totale du portefeuille"""
    if not client:
        return 0.0
        
    total = 0.0
    try:
        # Solde EUR
        eur_balance = float(client.get_asset_balance(asset='EUR')['free'])
        total += eur_balance
        
        # Cryptos
        for symbol in SYMBOLS:
            base_asset = symbol.replace('EUR', '')
            try:
                balance = float(client.get_asset_balance(asset=base_asset)['free'])
                if balance > 0:
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    price = float(ticker['price'])
                    total += balance * price
            except:
                continue
        return round(total, 2)
    except Exception as e:
        safe_print(f"ERREUR calcul portefeuille: {e}")
        return 0.0

def calculate_weekly_performance():
    """Calcule la performance hebdomadaire à partir de l'historique DB"""
    portfolio_history = load_portfolio_history()
    if not portfolio_history:
        return None
    
    # Convertir en DataFrame pour analyse
    times = [datetime.fromisoformat(k) for k in portfolio_history.keys()]
    values = list(portfolio_history.values())
    
    df = pd.DataFrame({'time': times, 'value': values})
    df = df.set_index('time')
    
    # Grouper par jour de la semaine
    df['day_of_week'] = df.index.day_name()
    df['date'] = df.index.date
    
    # Obtenir la valeur par jour (dernière valeur de chaque jour)
    daily_values = df.groupby('date')['value'].last()
    
    # Calculer les performances journalières
    daily_returns = daily_values.pct_change().dropna() * 100
    
    # Grouper par jour de la semaine
    daily_returns_df = pd.DataFrame({'date': daily_returns.index, 'return': daily_returns.values})
    daily_returns_df['day_of_week'] = daily_returns_df['date'].apply(lambda x: x.strftime('%A'))
    
    # Traduire les jours en français
    days_fr = {
        'Monday': 'Lundi',
        'Tuesday': 'Mardi', 
        'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi',
        'Friday': 'Vendredi',
        'Saturday': 'Samedi',
        'Sunday': 'Dimanche'
    }
    daily_returns_df['day_fr'] = daily_returns_df['day_of_week'].map(days_fr)
    
    # Moyenne par jour de la semaine
    weekly_performance = daily_returns_df.groupby('day_fr')['return'].mean()
    
    # Ordonner selon la semaine
    day_order = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    weekly_performance = weekly_performance.reindex(day_order, fill_value=0)
    
    return weekly_performance

@st.cache_data(ttl=60)  # Cache 60 secondes
def get_cached_data(symbol, interval, limit):
    """Récupère les données avec cache et pagination pour historique long"""
    if not client:
        return None
    try:
        all_klines = []
        
        # Si la limite demandée > 1000, on doit paginer
        # Binance limite à 1000 candles par appel
        # On calcule le nombre d'appels nécessaires
        
        end_time = None # Pour le premier appel (le plus récent)
        
        remaining_limit = limit
        
        while remaining_limit > 0:
            fetch_limit = min(remaining_limit, 1000)
            
            # Paramètres de l'appel
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': fetch_limit
            }
            if end_time:
                params['endTime'] = end_time
                
            klines = client.get_klines(**params)
            
            if not klines:
                break
                
            # Ajouter au début de la liste (on récupère en remontant le temps)
            all_klines = klines + all_klines
            
            remaining_limit -= len(klines)
            
            # Le prochain appel doit s'arrêter avant le début du bloc qu'on vient de recevoir
            # klines[0][0] est le timestamp de la première bougie du bloc
            end_time = klines[0][0] - 1
            
            if len(klines) < 1000: # Plus de données disponibles
                break
                
        if not all_klines:
            return None
            
        df = pd.DataFrame(all_klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Conversion types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        return df
        
    except Exception as e:
        safe_print(f"ERREUR données {symbol} {interval}: {e}")
        return None

def calculate_indicators(df):
    """Calcule les indicateurs techniques"""
    if df is None or df.empty:
        return df
        
    try:
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        # MAs
        df['ma20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
        df['ma50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
        df['ma200'] = ta.trend.SMAIndicator(df['close'], window=200).sma_indicator()
        # Bandes de Bollinger
        bollinger = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_high'] = bollinger.bollinger_hband()
        df['bb_low'] = bollinger.bollinger_lband()
        df['bb_middle'] = bollinger.bollinger_mavg()
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()
        return df
    except Exception as e:
        safe_print(f"ERREUR calcul indicateurs: {e}")
        return df

def get_market_sentiment():
    """Récupère le sentiment de marché général"""
    if not client:
        return "DÉCONNECTÉ", 0
        
    try:
        # Prix BTC comme indicateur de sentiment
        btc_data = get_cached_data('BTCEUR', Client.KLINE_INTERVAL_1DAY, 2)
        if btc_data is not None and len(btc_data) >= 2:
            change_24h = ((btc_data.iloc[-1]['close'] - btc_data.iloc[-2]['close']) / btc_data.iloc[-2]['close']) * 100
            
            if change_24h > 2:
                return "🟢 TRÈS HAUSSIER", change_24h
            elif change_24h > 0:
                return "🟡 HAUSSIER", change_24h
            elif change_24h > -2:
                return "🔴 BAISSIER", change_24h
            else:
                return "⚫ TRÈS BAISSIER", change_24h
    except Exception as e:
        safe_print(f"ERREUR sentiment marché: {e}")
    
    return "⚪ NEUTRE", 0

# --- INTERFACE UTILISATEUR ---
st.title("🚀 Dashboard Trading Pro - Base de Données Intégrée")
st.markdown("---")

# Vérification de la connexion
if not client:
    st.error("""
    **Connexion Binance échouée**
    
    Vérifiez que :
    - Vos clés API sont dans le fichier `.env`
    - Les clés sont valides pour le testnet Binance
    - Vous avez une connexion Internet
    """)
    st.stop()

# Sidebar
st.sidebar.header("🎯 Contrôles")

# --- GESTION DU BOT ---
import subprocess
import signal

def is_bot_running():
    """Vérifie si le bot est en cours d'exécution via le fichier PID"""
    try:
        if os.path.exists("bot.pid"):
            with open("bot.pid", "r") as f:
                pid = int(f.read().strip())
            # Vérifier si le processus existe
            try:
                os.kill(pid, 0)
                return True, pid
            except OSError:
                return False, None
        return False, None
    except:
        return False, None

def start_bot():
    """Démarre le bot"""
    try:
        if os.path.exists("bot.pid"):
            os.remove("bot.pid")
        
        # Nettoyer fichier signal s'il reste
        if os.path.exists(".stop_signal"):
            os.remove(".stop_signal")
            
        # Préparer l'environnement
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        # Lancer le processus
        process = subprocess.Popen(
            [sys.executable, "trading_engine.py"],
            cwd=os.getcwd(),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            env=env
        )
        
        # Sauvegarder le PID
        with open("bot.pid", "w") as f:
            f.write(str(process.pid))
            
        return True, "Bot démarré avec succès !"
    except Exception as e:
        return False, f"Erreur démarrage: {e}"

def stop_bot():
    """Arrête le bot proprement"""
    running, pid = is_bot_running()
    if running and pid:
        try:
            # 1. Créer le fichier signal pour arrêt gracieux
            with open(".stop_signal", "w") as f:
                f.write("STOP")
            
            # 2. Attendre que le bot s'arrête de lui-même (max 10s)
            for _ in range(10):
                running_check, _ = is_bot_running()
                if not running_check:
                    if os.path.exists("bot.pid"):
                        os.remove("bot.pid")
                    if os.path.exists(".stop_signal"):
                        os.remove(".stop_signal")
                    return True, "Bot arrêté proprement (avec message WhatsApp)."
                time.sleep(1)
            
            # 3. Si toujours pas arrêté, force kill
            os.kill(pid, signal.SIGTERM)
            if os.path.exists("bot.pid"):
                os.remove("bot.pid")
            if os.path.exists(".stop_signal"):
                os.remove(".stop_signal")
                
            return True, "Bot arrêté (forcé après délai)."
        except Exception as e:
            # Essayer force kill direct en cas d'erreur
            try:
                os.kill(pid, signal.SIGTERM) 
                return True, "Bot arrêté (forcé urgence)."
            except:
                return False, f"Erreur arrêt: {e}"
    return False, "Le bot n'est pas en cours d'exécution."

bot_running, bot_pid = is_bot_running()

if bot_running:
    st.sidebar.success(f"✅ BOT ACTIF (PID: {bot_pid})")
    if st.sidebar.button("🛑 ARRÊTER LE BOT", type="primary"):
        success, msg = stop_bot()
        if success:
            st.sidebar.success(msg)
            time.sleep(1)
            st.rerun()
        else:
            st.sidebar.error(msg)
else:
    st.sidebar.warning("🔴 BOT ARRÊTÉ")
    if st.sidebar.button("🚀 DÉMARRER LE BOT"):
        success, msg = start_bot()
        if success:
            st.sidebar.success(msg)
            time.sleep(1)
            st.rerun()
        else:
            st.sidebar.error(msg)

st.sidebar.markdown("---")

# --- ÉDITEUR DE CONFIGURATION ---
with st.sidebar.expander("⚙️ Configuration"):
    config = Config()
    
    with st.form("config_form"):
        new_amount = st.number_input("Montant par trade (€)", value=float(config.EURO_AMOUNT_PER_TRADE), min_value=10.0, step=1.0)
        new_stop_loss = st.number_input("Stop Loss (%)", value=float(config.STOP_LOSS_PERCENT), max_value=-0.1, step=0.1)
        new_take_profit = st.number_input("Take Profit (%)", value=float(config.TAKE_PROFIT_PERCENT), min_value=0.1, step=0.1)
        new_sleep_time = st.number_input("Intervalle Scan (s)", value=int(config.SLEEP_TIME), min_value=60, step=30)
        
        if st.form_submit_button("💾 Sauvegarder"):
            new_config = {
                "EURO_AMOUNT_PER_TRADE": new_amount,
                "STOP_LOSS_PERCENT": new_stop_loss,
                "TAKE_PROFIT_PERCENT": new_take_profit,
                "SLEEP_TIME": int(new_sleep_time)
            }
            if Config.save_dynamic_config(new_config):
                st.success("Configuration sauvegardée !")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Erreur sauvegarde")

st.sidebar.markdown("---")

selected_symbol = st.sidebar.selectbox("Crypto à analyser", SYMBOLS)

# Bouton de mise à jour manuelle
if st.sidebar.button("🔄 ACTUALISER", type="primary"):
    st.rerun()

# Note pour l'utilisateur
st.sidebar.caption("Cliquez pour mettre à jour les données")

# Métriques de performance
st.sidebar.header("📊 Performance")
portfolio_value = get_portfolio_value()
initial_investment = 1000  # À ajuster selon votre dépôt
profit_loss = portfolio_value - initial_investment
profit_loss_pct = (profit_loss / initial_investment) * 100

st.sidebar.metric("💰 Portefeuille", f"{portfolio_value:.2f}€")
st.sidebar.metric("📈 P&L Total", f"{profit_loss:+.2f}€", f"{profit_loss_pct:+.1f}%")

# Sentiment de marché
try:
    sa = SentimentAnalyzer()
    fng = sa.get_fear_and_greed_index()
    sentiment, btc_change = get_market_sentiment()
    
    st.sidebar.header("🌡️ Sentiment Marché")
    st.sidebar.info(f"{sentiment} | BTC: {btc_change:+.1f}%")
    
    if fng:
        st.sidebar.metric("Fear & Greed", f"{fng['value']}", f"{fng['classification']}")
except Exception as e:
    st.sidebar.error(f"Erreur sentiment: {e}")

# 1. VUE D'ENSEMBLE DU PORTEFEUILLE
st.header("📊 Évolution du Portefeuille (Base de Données)")

portfolio_history = update_portfolio_history()

if portfolio_history:
    times = [datetime.fromisoformat(k) for k in portfolio_history.keys()]
    values = list(portfolio_history.values())
    
    fig_portfolio = go.Figure()
    fig_portfolio.add_trace(go.Scatter(
        x=times, y=values,
        mode='lines+markers',
        name='Valeur Portefeuille',
        line=dict(color='#00ff88', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 136, 0.1)'
    ))
    
    # Ligne d'investissement initial
    fig_portfolio.add_hline(
        y=initial_investment, 
        line_dash="dash", 
        line_color="white",
        annotation_text="Investissement Initial"
    )
    
    fig_portfolio.update_layout(
        title=f"Évolution du Portefeuille ({len(portfolio_history)} points sauvegardés en DB)",
        xaxis_title="Temps",
        yaxis_title="Valeur (EUR)",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig_portfolio, use_container_width=True)
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Points sauvegardés", len(portfolio_history))
    with col2:
        first_date = times[0].strftime("%d/%m %H:%M")
        st.metric("Début tracking", first_date)
    with col3:
        if len(values) > 1:
            change_total = ((values[-1] - values[0]) / values[0]) * 100
            st.metric("Évolution totale", f"{change_total:+.1f}%")
else:
    st.info("📊 L'historique du portefeuille se construit...")

# 2. STATISTIQUES DE PERFORMANCE AVANCÉES
st.header("📈 Statistiques de Performance (Base de Données)")

# Récupérer les stats depuis la DB
performance_stats = get_performance_stats_from_db()

col1, col2, col3, col4 = st.columns(4)

with col1:
    if performance_stats:
        st.metric("Trades Total", performance_stats['total_trades'])
        st.metric("Win Rate", f"{performance_stats['win_rate']:.1f}%")
    else:
        st.metric("Rendement Total", f"{profit_loss_pct:+.1f}%", f"{profit_loss:+.2f}€")

with col2:
    if performance_stats:
        st.metric("P&L Moyen", f"{performance_stats['avg_pnl_percent']:+.2f}%")
        st.metric("P&L Total", f"{performance_stats['total_pnl_eur']:+.2f}€")
    else:
        if len(portfolio_history) > 1:
            returns = np.diff(list(portfolio_history.values()))
            sharpe = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")

with col3:
    if performance_stats:
        st.metric("Meilleur Trade", f"{performance_stats['best_trade']:+.2f}%")
        st.metric("Pire Trade", f"{performance_stats['worst_trade']:+.2f}%")
    else:
        if portfolio_history:
            values = list(portfolio_history.values())
            peak = max(values)
            current = values[-1]
            drawdown = ((current - peak) / peak) * 100
            st.metric("Drawdown Actuel", f"{drawdown:.1f}%")

with col4:
    entries = load_entry_prices()
    active_positions = len(entries)
    st.metric("Positions Actives", active_positions)

# 3. PERFORMANCE HEBDOMADAIRE
st.header("📅 Performance Hebdomadaire")

weekly_performance = calculate_weekly_performance()

if weekly_performance is not None and not weekly_performance.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Performance par Jour")
        fig_weekly = go.Figure(data=[go.Bar(
            x=weekly_performance.index,
            y=weekly_performance.values,
            marker_color=['green' if x > 0 else 'red' for x in weekly_performance.values],
            text=[f'{x:+.2f}%' for x in weekly_performance.values],
            textposition='auto'
        )])
        fig_weekly.update_layout(
            title="Performance Moyenne par Jour de la Semaine",
            xaxis_title="Jour",
            yaxis_title="Performance Moyenne (%)",
            template="plotly_dark",
            height=400
        )
        st.plotly_chart(fig_weekly, use_container_width=True)
    
    with col2:
        st.subheader("Répartition du Portefeuille")
        allocation_data = []
        
        # EUR
        try:
            eur_balance = float(client.get_asset_balance(asset='EUR')['free'])
            if eur_balance > 0.1:
                allocation_data.append(['EUR', eur_balance])
        except:
            pass
        
        # Cryptos
        for symbol in SYMBOLS:
            base_asset = symbol.replace('EUR', '')
            try:
                balance = float(client.get_asset_balance(asset=base_asset)['free'])
                if balance > 0.001:  # Minimum significatif
                    price = float(client.get_symbol_ticker(symbol=symbol)['price'])
                    value = balance * price
                    allocation_data.append([base_asset, value])
            except:
                continue
        
        if allocation_data:
            df_allocation = pd.DataFrame(allocation_data, columns=['Asset', 'Value'])
            fig_pie = go.Figure(data=[go.Pie(
                labels=df_allocation['Asset'], 
                values=df_allocation['Value'],
                hole=0.3
            )])
            fig_pie.update_layout(
                title="Répartition Actifs",
                template="plotly_dark", 
                height=400
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("💼 Aucun actif détecté")
else:
    st.info("📊 Données hebdomadaires en cours de collecte...")

# 4. ANALYSE TECHNIQUE COMPLÈTE
st.header(f"🔍 Analyse Technique - {selected_symbol}")

with st.spinner(f'Chargement des données pour {selected_symbol}...'):
    # Chargement des données pour les 3 timeframes (HISTORIQUE ÉTENDU)
    # 5m: 2500 * 5 = 12500 min = ~8.6 jours
    df_5m = get_cached_data(selected_symbol, Client.KLINE_INTERVAL_5MINUTE, 2500) 
    # 1h: 1000 * 1 = 1000 heures = ~41 jours
    df_1h = get_cached_data(selected_symbol, Client.KLINE_INTERVAL_1HOUR, 1000)   
    # 4h: 500 * 4 = 2000 heures = ~83 jours
    df_4h = get_cached_data(selected_symbol, Client.KLINE_INTERVAL_4HOUR, 500)
    
    if df_5m is not None:
        # Calcul des indicateurs pour chaque timeframe
        df_5m = calculate_indicators(df_5m)
        df_1h = calculate_indicators(df_1h) if df_1h is not None else None
        df_4h = calculate_indicators(df_4h) if df_4h is not None else None
        
        # Solde et position
        base_asset = selected_symbol.replace('EUR', '')
        try:
            balance = float(client.get_asset_balance(asset=base_asset)['free'])
        except:
            balance = 0.0

        entries = load_entry_prices()
        entry_price = entries.get(selected_symbol, 0)

        # Métriques depuis les données 5min (les plus récentes)
        last_row = df_5m.iloc[-1]
        current_price = last_row['close']
        rsi_val = last_row['rsi']
        macd_val = last_row['macd']

        # Affichage métriques
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Prix Actuel", f"{current_price:.2f} €")

        with col2:
            st.metric("Votre Solde", f"{balance:.4f} {base_asset}")

        with col3:
            rsi_color = "normal"
            if rsi_val < 30: 
                rsi_color = "off"
            elif rsi_val > 70: 
                rsi_color = "inverse"
            st.metric("RSI (14)", f"{rsi_val:.1f}", delta_color=rsi_color)

        with col4:
            macd_trend = "Haussier" if macd_val > 0 else "Baissier"
            st.metric("MACD", f"{macd_val:.4f}", macd_trend)

        with col5:
            if entry_price > 0:
                pnl = ((current_price - entry_price) / entry_price) * 100
                st.metric("P&L Position", f"{pnl:.1f}%", f"{pnl:+.1f}%")
            else:
                st.metric("Position", "Aucune")

        # GRAPHIQUES MULTI-TIMEFRAMES
        tab1, tab2, tab3 = st.tabs(["📈 5 Minutes", "⏰ 1 Heure", "📊 4 Heures"])

        with tab1:
            st.subheader("Analyse 5 Minutes")
            if df_5m is not None:
                fig_5m = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                      vertical_spacing=0.05, 
                                      row_heights=[0.6, 0.2, 0.2],
                                      subplot_titles=('Prix et indicateurs', 'MACD', 'RSI'))
                
                # Prix et MAs
                fig_5m.add_trace(go.Candlestick(x=df_5m['timestamp'], open=df_5m['open'], 
                                               high=df_5m['high'], low=df_5m['low'], 
                                               close=df_5m['close'], name="Prix"), row=1, col=1)
                fig_5m.add_trace(go.Scatter(x=df_5m['timestamp'], y=df_5m['ma20'], 
                                           line=dict(color='orange', width=1), name="MA 20"), row=1, col=1)
                fig_5m.add_trace(go.Scatter(x=df_5m['timestamp'], y=df_5m['ma50'], 
                                           line=dict(color='red', width=1), name="MA 50"), row=1, col=1)
                
                # MACD
                fig_5m.add_trace(go.Scatter(x=df_5m['timestamp'], y=df_5m['macd'], 
                                           line=dict(color='blue', width=2), name="MACD"), row=2, col=1)
                fig_5m.add_trace(go.Scatter(x=df_5m['timestamp'], y=df_5m['macd_signal'], 
                                           line=dict(color='red', width=1), name="Signal"), row=2, col=1)
                fig_5m.add_trace(go.Bar(x=df_5m['timestamp'], y=df_5m['macd_histogram'], 
                                       name="Histogramme", marker_color='gray'), row=2, col=1)
                
                # RSI
                fig_5m.add_trace(go.Scatter(x=df_5m['timestamp'], y=df_5m['rsi'], 
                                           line=dict(color='purple', width=2), name="RSI"), row=3, col=1)
                fig_5m.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                fig_5m.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
                fig_5m.add_hline(y=50, line_dash="dot", line_color="white", row=3, col=1)
                
                fig_5m.update_layout(height=800, xaxis_rangeslider_visible=False, template="plotly_dark")
                st.plotly_chart(fig_5m, use_container_width=True)
            else:
                st.error("Données 5 minutes non disponibles")

        with tab2:
            st.subheader("Analyse 1 Heure")
            if df_1h is not None:
                fig_1h = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                      vertical_spacing=0.05, 
                                      row_heights=[0.7, 0.3],
                                      subplot_titles=('Prix et tendance', 'RSI'))
                
                # Prix et MAs
                fig_1h.add_trace(go.Candlestick(x=df_1h['timestamp'], open=df_1h['open'], 
                                               high=df_1h['high'], low=df_1h['low'], 
                                               close=df_1h['close'], name="Prix"), row=1, col=1)
                fig_1h.add_trace(go.Scatter(x=df_1h['timestamp'], y=df_1h['ma50'], 
                                           line=dict(color='red', width=2), name="MA 50"), row=1, col=1)
                fig_1h.add_trace(go.Scatter(x=df_1h['timestamp'], y=df_1h['ma200'], 
                                           line=dict(color='purple', width=2), name="MA 200"), row=1, col=1)
                
                # RSI
                fig_1h.add_trace(go.Scatter(x=df_1h['timestamp'], y=df_1h['rsi'], 
                                           line=dict(color='orange', width=2), name="RSI"), row=2, col=1)
                fig_1h.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig_1h.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                fig_1h.add_hline(y=50, line_dash="dot", line_color="white", row=2, col=1)
                
                fig_1h.update_layout(height=600, xaxis_rangeslider_visible=False, template="plotly_dark")
                st.plotly_chart(fig_1h, use_container_width=True)
            else:
                st.warning("Données 1H non disponibles")

        with tab3:
            st.subheader("Analyse 4 Heures")
            if df_4h is not None:
                fig_4h = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                      vertical_spacing=0.05, 
                                      row_heights=[0.7, 0.3],
                                      subplot_titles=('Prix et tendance 4H', 'Indicateurs'))
                
                # Prix et MAs
                fig_4h.add_trace(go.Candlestick(x=df_4h['timestamp'], open=df_4h['open'], 
                                               high=df_4h['high'], low=df_4h['low'], 
                                               close=df_4h['close'], name="Prix 4H"), row=1, col=1)
                fig_4h.add_trace(go.Scatter(x=df_4h['timestamp'], y=df_4h['ma50'], 
                                           line=dict(color='red', width=2), name="MA 50"), row=1, col=1)
                fig_4h.add_trace(go.Scatter(x=df_4h['timestamp'], y=df_4h['ma200'], 
                                           line=dict(color='purple', width=2), name="MA 200"), row=1, col=1)
                
                # RSI
                fig_4h.add_trace(go.Scatter(x=df_4h['timestamp'], y=df_4h['rsi'], 
                                           line=dict(color='orange', width=2), name="RSI 4H"), row=2, col=1)
                fig_4h.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig_4h.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                fig_4h.add_hline(y=50, line_dash="dot", line_color="white", row=2, col=1)
                
                fig_4h.update_layout(height=600, xaxis_rangeslider_visible=False, template="plotly_dark")
                st.plotly_chart(fig_4h, use_container_width=True)
                
                # Analyse de tendance 4H
                if not df_4h.empty:
                    last_4h = df_4h.iloc[-1]
                    ma50_4h = last_4h['ma50']
                    ma200_4h = last_4h['ma200'] if 'ma200' in last_4h else None
                    
                    if not pd.isna(ma50_4h) and ma50_4h > 0:
                        trend_bullish = current_price > ma50_4h
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if trend_bullish:
                                st.success("🎯 TENDANCE 4H : HAUSSIÈRE")
                                st.info(f"Prix ({current_price:.2f}€) > MA50 ({ma50_4h:.2f}€)")
                            else:
                                st.error("⚠️ TENDANCE 4H : BAISSIÈRE")
                                st.info(f"Prix ({current_price:.2f}€) < MA50 ({ma50_4h:.2f}€)")
                        
                        with col2:
                            if ma200_4h and not pd.isna(ma200_4h):
                                if ma50_4h > ma200_4h:
                                    st.success("📈 MA50 > MA200 (Tendance forte)")
                                else:
                                    st.warning("📉 MA50 < MA200 (Tendance faible)")
            else:
                st.error("❌ Données 4H non disponibles")
                
    else:
        st.error(f"❌ Impossible de charger les données de base pour {selected_symbol}")

# 5. HISTORIQUE DES TRADES (BASE DE DONNÉES)
st.header("📋 Historique des Trades (Base de Données)")

trades_df = get_trade_history_from_db(limit=50)

if not trades_df.empty:
    # Formater l'affichage
    display_df = trades_df.copy()
    display_df['timestamp'] = pd.to_datetime(display_df['timestamp'])
    display_df = display_df.sort_values('timestamp', ascending=False)
    
    # Sélection des colonnes à afficher
    columns_to_show = ['timestamp', 'symbol', 'action', 'entry_price', 'exit_price', 'quantity', 'pnl_percent', 'reason']
    available_columns = [col for col in columns_to_show if col in display_df.columns]
    
    st.dataframe(
        display_df[available_columns].head(20),
        use_container_width=True,
        height=400
    )
    
    # Statistiques rapides
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trades", len(trades_df))
    with col2:
        winning_trades = len(trades_df[trades_df['pnl_percent'] > 0])
        st.metric("Trades Gagnants", winning_trades)
    with col3:
        avg_pnl = trades_df['pnl_percent'].mean() if not trades_df.empty else 0
        st.metric("P&L Moyen", f"{avg_pnl:+.2f}%")
else:
    st.info("📊 Aucun trade enregistré dans la base de données")

# 6. ANALYSE DE STRATÉGIE (BASE DE DONNÉES)
st.header("🎯 Analyse de Stratégie (Base de Données)")

strategy_analysis = get_strategy_analysis_from_db()

if strategy_analysis:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Performance par RSI")
        if strategy_analysis.get('rsi_performance'):
            rsi_df = pd.DataFrame(strategy_analysis['rsi_performance'])
            fig_rsi = go.Figure(data=[go.Bar(
                x=rsi_df['range'],
                y=rsi_df['win_rate'],
                text=[f"{x:.1f}%" for x in rsi_df['win_rate']],
                textposition='auto',
                marker_color=['green', 'red', 'blue']
            )])
            fig_rsi.update_layout(
                title="Win Rate par Niveau RSI",
                xaxis_title="Niveau RSI",
                yaxis_title="Win Rate (%)",
                template="plotly_dark"
            )
            st.plotly_chart(fig_rsi, use_container_width=True)
    
    with col2:
        st.subheader("Performance par Tendance")
        if strategy_analysis.get('trend_performance'):
            trend_df = pd.DataFrame(strategy_analysis['trend_performance'])
            fig_trend = go.Figure(data=[go.Bar(
                x=trend_df['trend'],
                y=trend_df['avg_pnl'],
                text=[f"{x:+.2f}%" for x in trend_df['avg_pnl']],
                textposition='auto',
                marker_color=['green' if x > 0 else 'red' for x in trend_df['avg_pnl']]
            )])
            fig_trend.update_layout(
                title="P&L Moyen par Tendance 4H",
                xaxis_title="Tendance",
                yaxis_title="P&L Moyen (%)",
                template="plotly_dark"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("📈 L'analyse de stratégie se construit avec les données...")

# 7. ALERTES ET POSITIONS
st.header("🚨 Alertes et Positions")

entries = load_entry_prices()
if entries:
    st.warning(f"Vous avez {len(entries)} positions ouvertes")
    
    for symbol, entry_price_val in list(entries.items()):
        try:
            current_price_val = float(client.get_symbol_ticker(symbol=symbol)['price'])
            pnl_val = ((current_price_val - entry_price_val) / entry_price_val) * 100
            
            if pnl_val <= -5:
                st.error(f"**{symbol}**: P&L {pnl_val:.1f}% - ⚠️ Stop Loss proche")
            elif pnl_val >= 8:
                st.success(f"**{symbol}**: P&L {pnl_val:.1f}% - 🎯 Take Profit proche")
            else:
                st.info(f"**{symbol}**: P&L {pnl_val:.1f}% - 📊 Position stable")
                
        except:
            st.info(f"**{symbol}**: En cours d'analyse...")
else:
    st.info("💼 Aucune position ouverte actuellement")

# 5. CLASSEMENT STRATÉGIES (LEADERBOARD)
st.header("🏆 Classement Stratégies (A/B Testing)")
st.caption("Comparaison en temps réel de la stratégie actuelle avec des variantes simulées (Paper Trading).")

leaderboard_data = get_leaderboard_from_db()

if leaderboard_data:
    # Créer un DataFrame pour l'affichage
    df_leaderboard = pd.DataFrame(leaderboard_data)
    
    # Renommer les colonnes pour l'affichage
    df_leaderboard.columns = ['Stratégie', 'Type', 'Trades', 'Win Rate (%)', 'P&L Moyen (%)', 'P&L Total']
    
    # Marquer la stratégie actuelle
    def highlight_real(row):
        return ['background-color: #1e3a2f' if row['Type'] == 'REAL' else '' for _ in row]

    st.dataframe(
        df_leaderboard.style.apply(highlight_real, axis=1)
        .format({
            "Win Rate (%)": "{:.1f}%",
            "P&L Moyen (%)": "{:+.2f}%", 
            "P&L Total": "{:+.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Afficher le meilleur challenger
    virtual_strats = [s for s in leaderboard_data if s['type'] == 'VIRTUAL']
    if virtual_strats:
        best_virtual = max(virtual_strats, key=lambda x: x['total_pnl'])
        
        current_strategy = next((s for s in leaderboard_data if s['type'] == 'REAL'), None)
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"💡 Meilleure Variante: **{best_virtual['name']}** avec {best_virtual['win_rate']:.1f}% de réussite.")
            
        with col2:
            if current_strategy and best_virtual['total_pnl'] > current_strategy['total_pnl']:
                diff = best_virtual['total_pnl'] - current_strategy['total_pnl']
                st.warning(f"⚠️ La variante surpasse la stratégie actuelle de {diff:.2f} points de profit !")
            else:
                st.success("✅ La stratégie actuelle est la plus performante !")

else:
    st.info("📉 En attente de données pour le classement (nécessite l'exécution du bot)...")

# Pied de page
st.markdown("---")
st.caption(f"🕒 Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')} | 🤖 Bot Trading Automatique | 🗃️ Base de Données SQLite | 🔒 Configuration sécurisée")