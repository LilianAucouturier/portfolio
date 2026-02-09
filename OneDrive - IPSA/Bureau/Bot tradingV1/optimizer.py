# -*- coding: utf-8 -*-
# optimizer.py - Optimisation automatique des paramètres
import pandas as pd
import ta
import json
import itertools
from rich.console import Console
from rich.table import Table

console = Console()

class StrategyOptimizer:
    def __init__(self, api_client):
        self.api_client = api_client
        self.output_file = "data/optimized_params.json"
        
    def get_market_data(self, symbol, interval, days=365):
        """Récupère l'historique COMPLET avec pagination (boucle)"""
        try:
            # 1. Calcul du start_time
            end_time = pd.Timestamp.now()
            start_time = end_time - pd.Timedelta(days=days)
            start_ts = int(start_time.timestamp() * 1000)
            
            console.print(f"📥 Téléchargement données {symbol} depuis {start_time.strftime('%Y-%m-%d')}...", style="blue")
            
            all_klines = []
            
            # 2. Boucle de récupération (Binance limite à 1000 par appel)
            while True:
                # Si on a déjà des données, on part du dernier timestamp
                current_start = start_ts if not all_klines else all_klines[-1][0] + 1
                
                klines = self.api_client.client.get_klines(
                    symbol=symbol, 
                    interval=interval, 
                    limit=1000,
                    startTime=current_start
                )
                
                if not klines:
                    break
                    
                all_klines.extend(klines)
                # console.print(f"   ... {len(all_klines)} bougies reçues", style="dim")
                
                # Si on a reçu moins de 1000 bougies, on est au bout (ou au présent)
                if len(klines) < 1000:
                    break
                    
                # Sécurité anti-boucle infinie (si on dépasse le présent)
                if all_klines[-1][0] > int(end_time.timestamp() * 1000):
                    break
            
            if not all_klines:
                return None
                
            # 3. Conversion DataFrame
            df = pd.DataFrame(all_klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Conversion types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            console.print(f"✅ Total: {len(df)} périodes chargées ({len(df)/24:.1f} jours)", style="green")
            return df
            
        except Exception as e:
            console.print(f"[ERREUR] Données {symbol}: {e}", style="red")
            return None

    def calculate_indicators(self, df, params):
        """Calcule les indicateurs avec DES PARAMÈTRES VARIABLES"""
        # Note: On recalcule tout ici pour éviter les effets de bord, 
        # mais pour la performance on pourrait optimiser.
        
        df = df.copy()
        
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
        
        # Bollinger Bands (Standard)
        bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()
        
        return df

    def run_backtest_simulation(self, df, params):
        """
        Simulation rapide pour un jeu de paramètres.
        Retourne le score de performance.
        """
        capital = 1000.0
        initial_capital = capital
        position = None
        trades_count = 0
        winning_trades = 0
        
        rsi_buy = params['rsi_oversold']
        rsi_sell = params['rsi_overbought']
        
        for i in range(20, len(df)):
            row = df.iloc[i]
            price = row['close']
            
            # LOGIQUE SIMPLIFIÉE (Doit matcher la stratégie réelle)
            signal = 'HOLD'
            
            # Achat
            if position is None:
                if row['rsi'] < rsi_buy and row['close'] < row['bb_low']:
                    signal = 'BUY'
            
            # Vente
            elif position is not None:
                if row['rsi'] > rsi_sell or row['close'] > row['bb_high']:
                    signal = 'SELL'
                
                # Stop Loss fixe pour l'optimisation
                entry = position['entry_price']
                if (price - entry) / entry < -0.05: 
                    signal = 'SELL' 

            # Exécution
            if signal == 'BUY' and position is None:
                qty = (capital * 0.99) / price
                position = {'entry_price': price, 'quantity': qty}
                capital -= qty * price
                
            elif signal == 'SELL' and position is not None:
                revenue = position['quantity'] * price * 0.999 # Frais 0.1%
                capital += revenue
                
                # Check win
                if revenue > (position['quantity'] * position['entry_price']):
                    winning_trades += 1
                
                trades_count += 1
                position = None
        
        # Revente finale
        if position:
            capital += position['quantity'] * df.iloc[-1]['close'] * 0.999
            
        return {
            'final_capital': capital,
            'trades': trades_count,
            'win_rate': (winning_trades / trades_count * 100) if trades_count > 0 else 0
        }

    def run_optimization(self, symbol="BTCUSDT"):
        """Lance la Grid Search"""
        console.print(f"\n[OPTIMISATION] Recherche des meilleurs paramètres pour {symbol}...", style="bold blue")
        
        # 1. Données (Sur 365 jours par défaut pour un bon training)
        df = self.get_market_data(symbol, '1h', days=365)
        if df is None:
            return
        
        # Pr-calcul des indicateurs fixes (RSI ne change pas, ce sont les seuils qui changent)
        # Pour optimiser la vitesse, on calcule RSI une fois
        df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
        bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()
        
        # 2. Espaces de recherche
        rsi_low_options = [20, 25, 30, 35]
        rsi_high_options = [65, 70, 75, 80]
        
        best_score = -float('inf')
        best_params = None
        best_result = None
        
        total_combinations = len(rsi_low_options) * len(rsi_high_options)
        console.print(f"Test de {total_combinations} combinaisons...", style="yellow")
        
        for rsi_l, rsi_h in itertools.product(rsi_low_options, rsi_high_options):
            params = {'rsi_oversold': rsi_l, 'rsi_overbought': rsi_h}
            
            res = self.run_backtest_simulation(df, params)
            
            # Score = Profit * WinRate (Simple metric)
            # On pénalise si trop peu de trades
            if res['trades'] < 5:
                score = 0
            else:
                profit = res['final_capital'] - 1000
                score = profit 
            
            if score > best_score:
                best_score = score
                best_params = params
                best_result = res
                
        # 3. Résultat
        if best_params:
            console.print("\n[SUCCES] Meilleurs paramètres trouvés :", style="green")
            console.print(f"RSI Oversold: {best_params['rsi_oversold']}")
            console.print(f"RSI Overbought: {best_params['rsi_overbought']}")
            console.print(f"Profit estimé: {best_result['final_capital'] - 1000:.2f} EUR")
            console.print(f"Win Rate: {best_result['win_rate']:.1f}%")
            
            # Sauvegarde
            self.save_params(best_params)
        else:
            console.print("Aucune combinaison viable trouvée.", style="red")

    def save_params(self, params):
        """Sauvegarde en JSON"""
        try:
            with open(self.output_file, 'w') as f:
                json.dump(params, f, indent=4)
            console.print(f"Paramètres sauvegardés dans {self.output_file}", style="green")
        except Exception as e:
            console.print(f"Erreur sauvegarde: {e}", style="red")

if __name__ == "__main__":
    from api_client import BinanceClient
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    client = BinanceClient()
    optimizer = StrategyOptimizer(client)
    optimizer.run_optimization("BTCUSDT")