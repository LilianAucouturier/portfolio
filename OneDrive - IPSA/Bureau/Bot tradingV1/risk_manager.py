# risk_manager.py
import pandas as pd
import numpy as np
from rich.console import Console

console = Console()

class RiskManager:
    def __init__(self, db):
        self.db = db
        self.max_drawdown_limit = -20.0 # %
        self.max_position_size_pct = 0.15 # 15% max par position
        
    def calculate_volatility(self, df, window=20):
        """Calcule la volatilité historique (écart-type des rendements)"""
        if df is None or len(df) < window:
            return 0.0
        
        df['returns'] = df['close'].pct_change()
        volatility = df['returns'].rolling(window=window).std().iloc[-1]
        return volatility * np.sqrt(365) * 100 # Annualisée approximative

    def calculate_var(self, portfolio_history, confidence_level=0.95):
        """Calcule la Value at Risk (VaR) historique"""
        if not portfolio_history or len(portfolio_history) < 30:
            return 0.0
            
        values = list(portfolio_history.values())
        returns = pd.Series(values).pct_change().dropna()
        
        if len(returns) == 0:
            return 0.0
            
        # VaR historique
        var = np.percentile(returns, (1 - confidence_level) * 100)
        return var * 100 # En pourcentage

    def calculate_max_drawdown(self, portfolio_history):
        """Calcule le Max Drawdown historique"""
        if not portfolio_history:
            return 0.0
            
        values = list(portfolio_history.values())
        peak = values[0]
        max_dd = 0.0
        
        for value in values:
            if value > peak:
                peak = value
            dd = (value - peak) / peak
            if dd < max_dd:
                max_dd = dd
                
        return max_dd * 100

    def check_portfolio_health(self, portfolio_value, open_positions):
        """Vérifie la santé du portefeuille et retourne des alertes"""
        alerts = []
        
        # 1. Vérification Drawdown
        history = self.db.get_portfolio_history(days=90)
        # Conversion format dict pour compatibilité
        history_dict = {row['timestamp']: row['total_value'] for _, row in history.iterrows()}
        
        current_dd = self.calculate_max_drawdown(history_dict)
        if current_dd < self.max_drawdown_limit:
            alerts.append(f"🚨 CRITIQUE: Max Drawdown dépassé ({current_dd:.2f}%)")
        elif current_dd < self.max_drawdown_limit / 2:
            alerts.append(f"⚠️ ATTENTION: Drawdown important ({current_dd:.2f}%)")
            
        # 2. Vérification Exposition
        if portfolio_value > 0:
            for symbol, entry_price in open_positions.items():
                # On aurait besoin de la quantité pour être précis, ici on suppose équi-répartition ou on ignore
                pass
                
        return alerts, current_dd

    def get_correlation_matrix(self, symbols, api_client, days=30):
        """Calcule la matrice de corrélation entre les actifs surveillés"""
        data = {}
        for symbol in symbols:
            df = api_client.get_market_data(symbol, '1d', days)
            if df is not None:
                data[symbol] = df['close']
        
        if data:
            df_corr = pd.DataFrame(data)
            return df_corr.corr()
        return pd.DataFrame()
