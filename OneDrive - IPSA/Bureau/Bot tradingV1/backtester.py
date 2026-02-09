# -*- coding: utf-8 -*-
# backtester.py - Version améliorée pour Backtesting sur données historiques
import pandas as pd
import ta
import numpy as np
import plotly.graph_objects as go
from rich.console import Console
from rich.table import Table

console = Console()

class Backtester:
    def __init__(self, api_client, strategy):
        self.api_client = api_client
        self.strategy = strategy
        self.initial_capital = 1000.0
        self.commission = 0.001  # 0.1% par trade (frais standard Binance)
    
    def get_historical_data(self, symbol, interval, limit=1000):
        """Récupère les données historiques"""
        try:
            # api_client.get_market_data retourne déjà un DataFrame formaté
            df = self.api_client.get_market_data(symbol, interval, limit)
            return df
        except Exception as e:
            console.print(f"[ERREUR] Données {interval}: {e}", style="red")
            return None

    def run(self, symbol, days=30):
        """Exécute le backtest complet"""
        console.print(f"\n[DEMARRAGE] Backtest sur {symbol} ({days} jours)", style="bold blue")
        
        # 1. Récupérer les données (1h et 4h)
        limit_1h = min(1000, days * 24 + 100)
        limit_4h = min(1000, days * 6 + 100)
        
        df_1h = self.get_historical_data(symbol, '1h', limit_1h)
        df_4h = self.get_historical_data(symbol, '4h', limit_4h)
        
        if df_1h is None or df_4h is None:
            console.print("[ERREUR] Impossible de récupérer les données", style="red")
            return None
            
        # 2. Calculer les indicateurs
        df_1h = self.strategy.calculate_indicators(df_1h)
        df_4h = self.strategy.calculate_indicators(df_4h)
        
        # 3. Préparer la boucle de simulation
        capital = self.initial_capital
        position = None 
        trades = []
        equity_curve = []
        timestamps = []
        
        # Mapping des dates 4H pour accès rapide
        df_4h.set_index('timestamp', inplace=True)
        
        console.print(f"[SIMULATION] {len(df_1h)} périodes...", style="yellow")
        
        for i in range(20, len(df_1h)): 
            row = df_1h.iloc[i]
            current_time = row['timestamp']
            current_price = row['close']
            
            # --- TENDANCE 4H ---
            try:
                resampled_time = current_time.floor('4h') 
                if resampled_time in df_4h.index:
                     trend_row = df_4h.loc[resampled_time]
                else:
                     trend_row = df_4h.iloc[df_4h.index.get_indexer([current_time], method='pad')[0]]
                
                ma50_4h = trend_row['ma50']
                market_is_bullish = current_price > ma50_4h if ma50_4h > 0 else False
                
            except:
                market_is_bullish = True 
            
            # --- LOGIQUE SIGNAL ---
            signal = 'HOLD'
            rsi_buy = self.strategy.rsi_oversold
            rsi_sell = self.strategy.rsi_overbought
            
            # LOGIQUE ACHAT
            if position is None:
                buy_conditions = 0
                if row['rsi'] < rsi_buy: buy_conditions += 1
                if row['close'] < row['bb_low']: buy_conditions += 1
                if row['stoch_rsi'] < 0.2: buy_conditions += 1
                if market_is_bullish: buy_conditions += 1
                
                if buy_conditions >= 3: 
                    signal = 'BUY'
            
            # LOGIQUE VENTE
            elif position is not None:
                sell_conditions = 0
                if row['rsi'] > rsi_sell: sell_conditions += 1
                if row['close'] > row['bb_high']: sell_conditions += 1
                if row['stoch_rsi'] > 0.8: sell_conditions += 1
                
                if sell_conditions >= 2:
                    signal = 'SELL'
            
            # TRAILING STOP
            if position:
                if current_price > position['highest_price']:
                    position['highest_price'] = current_price
                
                entry_price = position['entry_price']
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                
                if pnl_pct <= -5.0:
                    signal = "SELL_STOP_LOSS"
                
                drawdown_from_peak = ((current_price - position['highest_price']) / position['highest_price']) * 100
                if pnl_pct > 1.0 and drawdown_from_peak < -2.0:
                    signal = "SELL_TRAILING"

            # --- EXÉCUTION ---
            if signal == 'BUY' and position is None:
                amount = capital * 0.99
                quantity = amount / current_price
                fee = amount * self.commission
                capital -= (amount + fee)
                
                position = {
                    'entry_price': current_price,
                    'quantity': quantity,
                    'entry_time': current_time,
                    'highest_price': current_price
                }
                current_val = capital + (quantity * current_price)
                
            elif 'SELL' in signal and position is not None:
                quantity = position['quantity']
                revenue = quantity * current_price
                fee = revenue * self.commission
                new_capital_from_sale = revenue - fee
                
                capital += new_capital_from_sale
                
                pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
                
                trades.append({
                    'type': signal,
                    'entry_time': position['entry_time'],
                    'exit_time': current_time,
                    'entry_price': position['entry_price'],
                    'exit_price': current_price,
                    'pnl_pct': pnl_pct,
                    'capital': capital
                })
                
                position = None
                current_val = capital
                
            else:
                if position:
                    current_val = capital + (position['quantity'] * current_price)
                else:
                    current_val = capital
            
            equity_curve.append(current_val)
            timestamps.append(current_time)
            
        # Résumé Final
        final_capital = equity_curve[-1] if equity_curve else self.initial_capital
        total_perf = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        
        results = {
            'symbol': symbol,
            'initial': self.initial_capital,
            'final': final_capital,
            'perf': total_perf,
            'trades': trades,
            'equity': equity_curve,
            'timestamps': timestamps
        }
        
        self.generate_report(results)
        return results

    def generate_report(self, results):
        """Génère le rapport HTML et console"""
        # 1. Console
        table = Table(title=f"Rapport Backtest : {results['symbol']}")
        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="white")
        
        trades = results['trades']
        win_rate = len([t for t in trades if t['pnl_pct'] > 0]) / len(trades) * 100 if trades else 0
        
        table.add_row("Capital Final", f"{results['final']:.2f} EUR")
        table.add_row("Performance", f"{results['perf']:+.2f} %")
        table.add_row("Nb Trades", str(len(trades)))
        table.add_row("Win Rate", f"{win_rate:.1f} %")
        
        console.print(table)
        
        # 2. HTML
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=results['timestamps'], 
            y=results['equity'], 
            mode='lines', 
            name='Portefeuille (EUR)',
            line=dict(color='#00ff88', width=2)
        ))
        
        fig.update_layout(
            title=f"Backtest {results['symbol']} - Performance: {results['perf']:+.2f}%",
            template="plotly_dark",
            yaxis_title="Valeur Portfolio (EUR)"
        )
        
        filename = f"rapport_backtest_{results['symbol']}.html"
        fig.write_html(filename)
        console.print(f"[SUCCES] Rapport conserve: [link={filename}]{filename}[/link]", style="green")

if __name__ == "__main__":
    from api_client import BinanceClient
    from trading_strategy import TradingStrategy
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    client = BinanceClient()
    strategy = TradingStrategy()
    
    bt = Backtester(client, strategy)
    
    symbol = "BTCUSDT"
    bt.run(symbol, days=30)
