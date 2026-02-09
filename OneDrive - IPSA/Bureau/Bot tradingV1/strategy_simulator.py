# -*- coding: utf-8 -*-
import pandas as pd
import ta
from rich.console import Console

console = Console()

class StrategySimulator:
    def __init__(self, db):
        self.db = db
        self.strategies = {
            "Conservateur (RSI<25)": self.strategy_conservative,
            "Agressif (RSI<35)": self.strategy_aggressive,
            "Suivi Tendance": self.strategy_trend,
            "Williams %R": self.strategy_williams
        }
        
        # État des positions virtuelles : { "NomStratégie": { "BTCUSDT": { "entry_price": 50000, "quantity": 0.1 } } }
        self.virtual_positions = {}
        
        # Initialiser l'état
        for strat in self.strategies:
            self.virtual_positions[strat] = {}

    def calculate_indicators(self, df):
        """Calcule les indicateurs nécessaires pour la simulation"""
        if df is None or df.empty:
            return df
            
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        # MAs
        df['ma20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
        df['ma50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
        
        # Williams %R
        df['williams_r'] = ta.momentum.WilliamsRIndicator(df['high'], df['low'], df['close']).williams_r()
        
        return df

    def evaluate_strategies(self, symbol, df_5m):
        """Évalue toutes les stratégies virtuelles pour une paire donnée"""
        try:
            if df_5m is None or len(df_5m) < 50:
                return

            last_row = df_5m.iloc[-1]
            current_price = last_row['close']
            
            # Pour chaque stratégie, vérifier les signaux
            for strat_name, strat_func in self.strategies.items():
                signal = strat_func(last_row)
                
                # Gestion des positions virtuelles
                positions = self.virtual_positions[strat_name]
                is_in_position = symbol in positions
                
                # LOGIQUE ACHAT
                if signal == 'BUY' and not is_in_position:
                    # Simuler un achat (mise fixe de 100€ pour comparer)
                    quantity = 100.0 / current_price
                    positions[symbol] = {
                        "entry_price": current_price,
                        "quantity": quantity
                    }
                    
                    self.db.log_virtual_trade(strat_name, symbol, "BUY", current_price, quantity, 0, "Signal Virtuel")
                    # console.print(f"👻 [Virtuel] {strat_name} ACHAT {symbol} @ {current_price}", style="dim")

                # LOGIQUE VENTE
                elif signal == 'SELL' and is_in_position:
                    entry_data = positions[symbol]
                    entry_price = entry_data['entry_price']
                    quantity = entry_data['quantity']
                    
                    pnl_percent = ((current_price - entry_price) / entry_price) * 100
                    
                    del positions[symbol]
                    
                    self.db.log_virtual_trade(strat_name, symbol, "SELL", current_price, quantity, pnl_percent, "Signal Virtuel")
                    # console.print(f"👻 [Virtuel] {strat_name} VENTE {symbol} @ {current_price} (P&L: {pnl_percent:.2f}%)", style="dim")

                # STOP LOSS VIRTUEL (-5%)
                elif is_in_position:
                    entry_price = positions[symbol]['entry_price']
                    current_pnl = ((current_price - entry_price) / entry_price) * 100
                    
                    if current_pnl <= -5.0:
                        del positions[symbol]
                        self.db.log_virtual_trade(strat_name, symbol, "SELL", current_price, 0, current_pnl, "Stop Loss Virtuel")

        except Exception as e:
            console.print(f"❌ Erreur simulateur {symbol}: {e}", style="red")

    # --- DÉFINITION DES STRATÉGIES ---
    
    def strategy_conservative(self, row):
        # Achat RSI < 25, Vente RSI > 65
        if row['rsi'] < 25: return 'BUY'
        if row['rsi'] > 65: return 'SELL'
        return 'HOLD'

    def strategy_aggressive(self, row):
        # Achat RSI < 35, Vente RSI > 75
        if row['rsi'] < 35: return 'BUY'
        if row['rsi'] > 75: return 'SELL'
        return 'HOLD'

    def strategy_trend(self, row):
        # Achat si MA20 > MA50 (tendance haussière) et repli (RSI < 45)
        # Vente si RSI > 70 ou croisement baissier
        if row['ma20'] > row['ma50'] and row['rsi'] < 45: return 'BUY'
        if row['rsi'] > 70: return 'SELL'
        return 'HOLD'

    def strategy_williams(self, row):
        # Williams %R : Achat < -80, Vente > -20
        if row['williams_r'] < -80: return 'BUY'
        if row['williams_r'] > -20: return 'SELL'
        return 'HOLD'
