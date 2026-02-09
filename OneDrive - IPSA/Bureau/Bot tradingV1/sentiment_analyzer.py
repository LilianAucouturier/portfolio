# -*- coding: utf-8 -*-
import json
import urllib.request
from rich.console import Console

console = Console()

class SentimentAnalyzer:
    def __init__(self):
        self.fng_url = "https://api.alternative.me/fng/"
        
    def get_fear_and_greed_index(self):
        """Récupère l'indice Fear & Greed Crypto"""
        try:
            with urllib.request.urlopen(self.fng_url) as response:
                data = json.loads(response.read().decode())
                
            if data['metadata']['error'] is None:
                item = data['data'][0]
                value = int(item['value'])
                classification = item['value_classification']
                
                # Emoji
                emoji = "NEUTRE"
                if value >= 75: emoji = "EXTREME GREED" 
                elif value >= 55: emoji = "GREED" 
                elif value <= 25: emoji = "EXTREME FEAR" 
                elif value <= 45: emoji = "FEAR" 
                
                return {
                    'value': value,
                    'classification': classification,
                    'emoji': emoji,
                    'timestamp': item['timestamp']
                }
            return None
        except Exception as e:
            console.print(f"Erreur Fear&Greed: {e}", style="red")
            return None

    def analyze_market_sentiment(self, btc_change_24h):
        """Combine Fear&Greed avec la variation BTC"""
        fng = self.get_fear_and_greed_index()
        
        sentiment_score = 0
        details = []
        
        # 1. Analyse F&G
        if fng:
            details.append(f"Fear & Greed: {fng['value']} ({fng['classification']})")
            if fng['value'] < 20: sentiment_score -= 2 # Extreme Fear -> Achat potentiel (contrarian) ou Panic
            elif fng['value'] > 80: sentiment_score -= 2 # Extreme Greed -> Vente potentielle (top)
            elif fng['value'] > 60: sentiment_score += 1 # Bullish
            elif fng['value'] < 40: sentiment_score -= 1 # Bearish
            
        # 2. Analyse BTC Trend
        if btc_change_24h > 5:
            sentiment_score += 2
            details.append("BTC Pump (>5%)")
        elif btc_change_24h > 0:
            sentiment_score += 1
            details.append("BTC Haussier")
        elif btc_change_24h < -5:
            sentiment_score -= 2
            details.append("BTC Dump (<-5%)")
        else:
            sentiment_score -= 1
            details.append("BTC Baissier")
            
        # Conclusion
        if sentiment_score >= 2:
            return "TRES HAUSSIER", details
        elif sentiment_score >= 1:
            return "HAUSSIER", details
        elif sentiment_score <= -2:
            return "TRES BAISSIER", details
        elif sentiment_score <= -1:
            return "BAISSIER", details
        else:
            return "NEUTRE", details

if __name__ == "__main__":
    sa = SentimentAnalyzer()
    print(sa.get_fear_and_greed_index())
