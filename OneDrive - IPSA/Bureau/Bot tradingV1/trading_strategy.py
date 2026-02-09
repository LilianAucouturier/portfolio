import pandas as pd
import ta
import json
import os
import numpy as np
from config import Config
from rich.console import Console

console = Console()

class TradingStrategy:
    def __init__(self):
        console.print("📊 Stratégie de trading initialisée", style="blue")
        
        # Paramètres par défaut
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.ma_fast = 20
        self.ma_slow = 50
        
        # Charge automatiquement les paramètres optimisés
        self.load_optimized_params()
    
    def load_optimized_params(self):
        """Charge les paramètres optimisés depuis le fichier JSON"""
        try:
            params_file = "data/optimized_params.json"
            
            if os.path.exists(params_file):
                with open(params_file, 'r') as f:
                    params = json.load(f)
                
                # Met à jour les variables avec les paramètres optimisés
                self.rsi_oversold = params.get('rsi_oversold', self.rsi_oversold)
                self.rsi_overbought = params.get('rsi_overbought', self.rsi_overbought)
                self.ma_fast = params.get('ma_fast', self.ma_fast)
                self.ma_slow = params.get('ma_slow', self.ma_slow)
                
                console.print(f"✅ Paramètres optimisés chargés: RSI {self.rsi_oversold}/{self.rsi_overbought}, MA {self.ma_fast}/{self.ma_slow}", style="green")
            else:
                console.print(f"⚙️  Paramètres par défaut: RSI {self.rsi_oversold}/{self.rsi_overbought}", style="blue")
                
        except Exception as e:
            console.print(f"❌ Erreur chargement paramètres: {e}", style="red")
    
    def calculate_indicators(self, df):
        """
        Calcule tous les indicateurs techniques sur le DataFrame
        """
        try:
            # Vérifier que le DataFrame n'est pas vide
            if df is None or df.empty:
                console.print("❌ DataFrame vide pour calcul des indicateurs", style="red")
                return df
            
            # Conversion des colonnes en float pour éviter les erreurs
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # === INDICATEURS DE MOMENTUM ===
            
            # RSI (Relative Strength Index)
            df['rsi'] = ta.momentum.RSIIndicator(
                close=df['close'], 
                window=14
            ).rsi()
            
            # Stochastic RSI
            df['stoch_rsi'] = ta.momentum.StochRSIIndicator(
                close=df['close'],
                window=14,
                smooth1=3,
                smooth2=3
            ).stochrsi()
            
            # MACD (Moving Average Convergence Divergence)
            macd = ta.trend.MACD(close=df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_histogram'] = macd.macd_diff()
            
            # Williams %R
            df['williams_r'] = ta.momentum.WilliamsRIndicator(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                lbp=14
            ).williams_r()
            
            # === INDICATEURS DE TENDANCE ===
            
            # Moving Averages
            df['ma20'] = ta.trend.SMAIndicator(close=df['close'], window=20).sma_indicator()
            df['ma50'] = ta.trend.SMAIndicator(close=df['close'], window=50).sma_indicator()
            df['ma100'] = ta.trend.SMAIndicator(close=df['close'], window=100).sma_indicator()
            df['ma200'] = ta.trend.SMAIndicator(close=df['close'], window=200).sma_indicator()
            
            # EMA (Exponential Moving Average)
            df['ema12'] = ta.trend.EMAIndicator(close=df['close'], window=12).ema_indicator()
            df['ema26'] = ta.trend.EMAIndicator(close=df['close'], window=26).ema_indicator()
            
            # Ichimoku Cloud (simplifié)
            ichimoku = ta.trend.IchimokuIndicator(
                high=df['high'],
                low=df['low'],
                window1=9,
                window2=26,
                window3=52
            )
            df['ichimoku_base'] = ichimoku.ichimoku_base_line()
            df['ichimoku_conversion'] = ichimoku.ichimoku_conversion_line()
            
            # === INDICATEURS DE VOLATILITÉ ===
            
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(
                close=df['close'], 
                window=20, 
                window_dev=2
            )
            df['bb_high'] = bollinger.bollinger_hband()
            df['bb_low'] = bollinger.bollinger_lband()
            df['bb_middle'] = bollinger.bollinger_mavg()
            df['bb_width'] = bollinger.bollinger_wband()  # Largeur des bandes
            df['bb_position'] = (df['close'] - df['bb_low']) / (df['bb_high'] - df['bb_low'])  # Position dans les bandes
            
            # ATR (Average True Range) - mesure de volatilité
            df['atr'] = ta.volatility.AverageTrueRange(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                window=14
            ).average_true_range()
            
            # === INDICATEURS DE VOLUME ===
            
            # Volume Weighted Average Price
            df['vwap'] = ta.volume.VolumeWeightedAveragePrice(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                volume=df['volume'],
                window=14
            ).volume_weighted_average_price()
            
            # On Balance Volume
            df['obv'] = ta.volume.OnBalanceVolumeIndicator(
                close=df['close'],
                volume=df['volume']
            ).on_balance_volume()
            
            # Force Index
            df['force_index'] = ta.volume.ForceIndexIndicator(
                close=df['close'],
                volume=df['volume'],
                window=13
            ).force_index()
            
            # Nettoyage des valeurs NaN
            df = df.fillna(0)
            
            return df
            
        except Exception as e:
            console.print(f"❌ Erreur calcul indicateurs: {e}", style="red")
            return df
    
    def get_trend_signal(self, df_daily):
        """
        Détermine la tendance de fond basée sur plusieurs indicateurs
        """
        try:
            if df_daily is None or len(df_daily) < 20:
                return True,  "[yellow]En analyse...[/yellow]"
            
            last_row = df_daily.iloc[-1]
            
            # Vérifications de base
            if last_row['ma50'] == 0 or pd.isna(last_row['ma50']):
                return True, "[yellow]Calcul en cours...[/yellow]"
            
            current_price = last_row['close']
            ma50 = last_row['ma50']
            ma200 = last_row['ma200']
            
            # === CONFLUENCE POUR LA TENDANCE ===
            
            bullish_signals = 0
            total_signals = 0
            
            # 1. Prix au-dessus de MA50
            if current_price > ma50:
                bullish_signals += 1
            total_signals += 1
            
            # 2. Prix au-dessus de MA200 (tendance long terme)
            if ma200 > 0 and current_price > ma200:
                bullish_signals += 1
            total_signals += 1
            
            # 3. MA50 au-dessus de MA200 (Golden Cross)
            if ma200 > 0 and ma50 > ma200:
                bullish_signals += 1
            total_signals += 1
            
            # 4. RSI > 50 (momentum positif)
            if last_row['rsi'] > 50:
                bullish_signals += 1
            total_signals += 1
            
            # 5. MACD au-dessus de sa ligne de signal
            if last_row['macd'] > last_row['macd_signal']:
                bullish_signals += 1
            total_signals += 1
            
            # Calcul du score de tendance
            trend_score = bullish_signals / total_signals
            
            # Détermination de la tendance
            if trend_score >= 0.7:  # 70% des signaux sont haussiers
                return True, f"[green]FORT Haussière ({bullish_signals}/{total_signals})[/green]"
            elif trend_score >= 0.5:  # 50-69% des signaux sont haussiers
                return True, f"[green]Haussière ({bullish_signals}/{total_signals})[/green]"
            elif trend_score >= 0.3:  # 30-49% des signaux sont haussiers
                return False, f"[red]Baissière ({bullish_signals}/{total_signals})[/red]"
            else:  # Moins de 30% des signaux sont haussiers
                return False, f"[red]FORT Baissière ({bullish_signals}/{total_signals})[/red]"
                
        except Exception as e:
            console.print(f"❌ Erreur analyse tendance: {e}", style="red")
            return False, "[red]Erreur Tendance[/red]"

    def predict_price_trend(self, df, lookback=30):
        """
        Prédiction de tendance basique avec régression linéaire (ML simple)
        Retourne: 'UP', 'DOWN', 'FLAT' et la confiance
        """
        try:
            if df is None or len(df) < lookback:
                return 'FLAT', 0.0
            
            # Utiliser les N derniers points de clôture
            data = df['close'].tail(lookback).values
            x = np.arange(len(data))
            
            # Régression linéaire simple (y = mx + c)
            # m est la pente (slope)
            slope, intercept = np.polyfit(x, data, 1)
            
            # Calcul du R-squared pour la confiance
            y_pred = slope * x + intercept
            residuals = data - y_pred
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((data - np.mean(data))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # Normaliser la pente par rapport au prix moyen (pourcentage de changement par période)
            avg_price = np.mean(data)
            normalized_slope = (slope / avg_price) * 100
            
            # Seuils de décision
            if normalized_slope > 0.05: # > 0.05% par période
                return 'UP', r_squared
            elif normalized_slope < -0.05:
                return 'DOWN', r_squared
            else:
                return 'FLAT', r_squared
                
        except Exception as e:
            console.print(f"❌ Erreur prédiction ML: {e}", style="red")
            return 'FLAT', 0.0
    
    def get_trading_signal(self, df, is_in_position, market_is_bullish):
        """
        Génère le signal de trading final avec confluence d'indicateurs
        Utilise AUTOMATIQUEMENT les paramètres optimisés
        """
        try:
            if df is None or len(df) < 20:
                return 'HOLD'
            
            last_row = df.iloc[-1]
            current_price = last_row['close']
            
            # === PRÉDICTION ML ===
            ml_trend, ml_confidence = self.predict_price_trend(df)
            
            # === CONDITIONS D'ACHAT (Confluence) ===
            buy_conditions = []
            
            # ✅ RSI oversold AVEC PARAMÈTRES OPTIMISÉS
            buy_conditions.append(last_row['rsi'] < self.rsi_oversold)
            
            # Prix en dessous de la Bollinger Band inférieure
            buy_conditions.append(last_row['close'] <= last_row['bb_low'])
            
            # Williams %R oversold
            buy_conditions.append(last_row['williams_r'] <= -80)
            
            # Stochastic RSI oversold
            buy_conditions.append(last_row['stoch_rsi'] < 0.2)
            
            # Prix au-dessus de VWAP (confirmation momentum)
            buy_conditions.append(last_row['close'] > last_row['vwap'])
            
            # ✅ ML Confirmation
            if ml_trend == 'UP' and ml_confidence > 0.5:
                buy_conditions.append(True)
            
            # Compter les conditions remplies
            buy_signals = sum(buy_conditions)
            total_buy_conditions = len(buy_conditions) # Maintenant 6 avec ML
            
            # === CONDITIONS DE VENTE (Confluence) ===
            sell_conditions = []
            
            # ✅ RSI overbought AVEC PARAMÈTRES OPTIMISÉS
            sell_conditions.append(last_row['rsi'] > self.rsi_overbought)
            
            # Prix au-dessus de la Bollinger Band supérieure
            sell_conditions.append(last_row['close'] >= last_row['bb_high'])
            
            # Williams %R overbought
            sell_conditions.append(last_row['williams_r'] >= -20)
            
            # Stochastic RSI overbought
            sell_conditions.append(last_row['stoch_rsi'] > 0.8)
            
            # MACD croisement baissier
            sell_conditions.append(last_row['macd'] < last_row['macd_signal'])
            
            # ✅ ML Confirmation
            if ml_trend == 'DOWN' and ml_confidence > 0.5:
                sell_conditions.append(True)
            
            # Compter les conditions remplies
            sell_signals = sum(sell_conditions)
            total_sell_conditions = len(sell_conditions) # Maintenant 6 avec ML
            
            # === LOGIQUE DE DÉCISION ===
            
            # SIGNAL D'ACHAT : 
            # - Pas en position
            # - Marché haussier (filtre de tendance)
            # - Au moins 60% des conditions d'achat remplies
            if (not is_in_position and 
                market_is_bullish and 
                buy_signals >= total_buy_conditions * 0.6):
                console.print(f"🎯 SIGNAL ACHAT: {buy_signals}/{total_buy_conditions} conditions (RSI: {last_row['rsi']:.1f} < {self.rsi_oversold}) | ML: {ml_trend}", style="green")
                return 'BUY'
            
            # SIGNAL DE VENTE :
            # - En position
            # - Au moins 60% des conditions de vente remplies
            elif (is_in_position and 
                  sell_signals >= total_sell_conditions * 0.6):
                console.print(f"🎯 SIGNAL VENTE: {sell_signals}/{total_sell_conditions} conditions (RSI: {last_row['rsi']:.1f} > {self.rsi_overbought}) | ML: {ml_trend}", style="yellow")
                return 'SELL'
            
            # SIGNAL DE VENTE URGENTE :
            # - RSI extrêmement overbought
            elif (is_in_position and 
                  last_row['rsi'] > 85):
                console.print(f"🚨 VENTE URGENTE: RSI {last_row['rsi']:.1f}", style="red")
                return 'SELL'
            
            else:
                return 'HOLD'
                
        except Exception as e:
            console.print(f"❌ Erreur génération signal: {e}", style="red")
            return 'HOLD'
    
    def get_support_resistance_levels(self, df, num_levels=3):
        """
        Identifie les niveaux de support et résistance
        """
        try:
            if df is None or len(df) < 50:
                return [], []
            
            # Méthode simple basée sur les plus hauts/plus bas récents
            window = 20
            highs = df['high'].rolling(window=window).max()
            lows = df['low'].rolling(window=window).min()
            
            # Derniers niveaux significatifs
            resistance_levels = highs.nlargest(num_levels).unique().tolist()
            support_levels = lows.nsmallest(num_levels).unique().tolist()
            
            return support_levels, resistance_levels
            
        except Exception as e:
            console.print(f"❌ Erreur niveaux S/R: {e}", style="red")
            return [], []
    
    def calculate_position_size(self, current_price, portfolio_value, risk_per_trade=0.02):
        """
        Calcule la taille de position basée sur la gestion du risque
        risk_per_trade: 2% du portefeuille par défaut
        """
        try:
            risk_amount = portfolio_value * risk_per_trade
            # Position size basée sur le prix actuel
            position_size = risk_amount / current_price
            return position_size
            
        except Exception as e:
            console.print(f"❌ Erreur calcul taille position: {e}", style="red")
            return 0
    
    def get_market_strength(self, df):
        """
        Évalue la force globale du marché
        """
        try:
            if df is None or len(df) < 20:
                return "NEUTRE", 50
            
            last_row = df.iloc[-1]
            
            strength_score = 0
            total_indicators = 0
            
            # RSI strength
            if last_row['rsi'] > 60:
                strength_score += 1
            elif last_row['rsi'] < 40:
                strength_score -= 1
            total_indicators += 1
            
            # MACD strength
            if last_row['macd'] > last_row['macd_signal']:
                strength_score += 1
            else:
                strength_score -= 1
            total_indicators += 1
            
            # Volume strength (OBV)
            if len(df) > 1:
                prev_obv = df.iloc[-2]['obv']
                if last_row['obv'] > prev_obv:
                    strength_score += 1
                else:
                    strength_score -= 1
                total_indicators += 1
            
            # Normalisation du score
            normalized_score = (strength_score / total_indicators + 1) * 50
            
            if normalized_score >= 70:
                return "FORT", normalized_score
            elif normalized_score >= 55:
                return "MODÉRÉ", normalized_score
            elif normalized_score >= 45:
                return "NEUTRE", normalized_score
            elif normalized_score >= 30:
                return "FAIBLE", normalized_score
            else:
                return "TRÈS FAIBLE", normalized_score
                
        except Exception as e:
            console.print(f"❌ Erreur force marché: {e}", style="red")
            return "INCONNU", 50

# Fonction utilitaire pour analyser une paire rapidement
def quick_analysis(api_client, symbol, strategy):
    """
    Analyse rapide d'une paire pour debug
    """
    try:
        console.print(f"\n🔍 Analyse rapide: {symbol}", style="bold blue")
        
        # Données 5min
        df_5min = api_client.get_market_data(symbol, '5m', 100)
        if df_5min is not None:
            df_5min = strategy.calculate_indicators(df_5min)
            last = df_5min.iloc[-1]
            
            console.print(f"Prix: {last['close']:.2f}€ | RSI: {last['rsi']:.1f} | BB Pos: {last['bb_position']:.2f}")
            
            # Tendance 4H
            df_4h = api_client.get_market_data(symbol, '4h', 100)
            if df_4h is not None:
                df_4h = strategy.calculate_indicators(df_4h)
                trend_bullish, trend_text = strategy.get_trend_signal(df_4h)
                console.print(f"Tendance 4H: {trend_text}")
        
    except Exception as e:
        console.print(f"❌ Erreur analyse rapide: {e}", style="red")