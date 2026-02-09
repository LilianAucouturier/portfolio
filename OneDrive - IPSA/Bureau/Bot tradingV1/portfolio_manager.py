import json
import os
from rich.console import Console

console = Console()

class PortfolioManager:
    def __init__(self, api_client, db):
        self.api_client = api_client
        self.db = db
        self.entry_prices = self.load_entry_prices()
    
    def detect_available_symbols(self):
        """Détecte automatiquement les paires EUR disponibles"""
        try:
            exchange_info = self.api_client.safe_api_call(self.api_client.client.get_exchange_info)
            if not exchange_info:
                return self.get_fallback_symbols()
            
            eur_pairs = []
            for symbol in exchange_info['symbols']:
                if (symbol['symbol'].endswith('EUR') and 
                    symbol['status'] == 'TRADING' and
                    symbol['quoteAsset'] == 'EUR' and 
                    symbol['isSpotTradingAllowed'] and
                    symbol['baseAsset'] != 'EUR'):
                    eur_pairs.append(symbol['symbol'])
            
            eur_pairs.sort() 
            console.print(f"   🔍 {len(eur_pairs)} paires EUR disponibles", style="bold green")
            
            if eur_pairs: 
                console.print(f"   📋 Exemples: {', '.join(eur_pairs[:10])}", style="dim")
            return eur_pairs
            
        except Exception as e:
            console.print(f"   ⚠️  Détection auto échouée: {e}", style="yellow")
            return self.get_fallback_symbols()
    
    def get_fallback_symbols(self):
        """Liste de secours des paires EUR"""
        return [
            'BTCEUR', 'ETHEUR', 'BNBEUR', 'SOLEUR', 'XRPEUR', 
            'AVAXEUR', 'DOTEUR', 'ATOMEUR', 'TRXEUR', 'LINKEUR', 
            'LTCEUR', 'XLMEUR'
        ]
    
    def load_entry_prices(self):
        """Charge les prix d'entrée depuis la base de données"""
        try:
            trades_df = self.db.get_trade_history(limit=1000)
            if trades_df.empty:
                console.print("   📊 Aucun trade historique trouvé", style="blue")
                return {}
            
            available_symbols = self.detect_available_symbols()
            open_positions = {}
            
            for symbol in available_symbols:
                try:
                    symbol_trades = trades_df[trades_df['symbol'] == symbol]
                    if symbol_trades.empty:
                        continue
                    
                    buys = symbol_trades[symbol_trades['action'].str.contains('ACHAT|BUY', case=False, na=False)]
                    sells = symbol_trades[symbol_trades['action'].str.contains('VENTE|SELL|STOP_LOSS|TAKE_PROFIT', case=False, na=False)]
                    
                    if len(buys) > len(sells) and not buys.empty:
                        last_buy = buys.iloc[-1]  # Prendre le dernier achat
                        entry_price = last_buy.get('entry_price')
                        if entry_price and entry_price > 0:
                            open_positions[symbol] = float(entry_price)
                            console.print(f"   📈 Position: {symbol} @ {entry_price:.2f}€", style="green")
                            
                except Exception as e:
                    console.print(f"   ⚠️  Erreur {symbol}: {e}", style="yellow")
                    continue
            
            console.print(f"   ✅ {len(open_positions)} positions ouvertes chargées", style="green")
            return open_positions
            
        except Exception as e:
            console.print(f"   ❌ Erreur chargement DB: {e}", style="red")
            return self.load_entry_prices_backup()
    
    def load_entry_prices_backup(self):
        """Charge les prix d'entrée depuis le fichier JSON de secours"""
        try:
            if os.path.exists("data/entry_prices.json"):
                with open("data/entry_prices.json", 'r') as f:
                    backup_data = json.load(f)
                    console.print(f"   📁 Backup chargé: {len(backup_data)} positions", style="yellow")
                    return backup_data
            return {}
        except:
            return {}
    
    def save_entry_prices(self):
        """Sauvegarde les prix d'entrée en backup JSON"""
        try:
            os.makedirs('data', exist_ok=True)
            with open("data/entry_prices.json", 'w') as f:
                json.dump(self.entry_prices, f, indent=4)
        except Exception as e:
            console.print(f"   ⚠️  Erreur sauvegarde backup: {e}", style="yellow")
    
    def update_portfolio_value(self, symbols_to_scan=None):
        """Calcule la valeur totale du portefeuille"""
        try:
            account = self.api_client.safe_api_call(self.api_client.client.get_account)
            if not account:
                console.print("   ❌ Impossible de récupérer le compte", style="red")
                return 0.0
            
            total_value = 0.0
            
            # Déterminer les symboles à scanner
            if symbols_to_scan:
                symbols = symbols_to_scan
            else:
                symbols = self.detect_available_symbols()
            
            # Traiter chaque balance
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total_balance = free + locked
                
                if total_balance <= 0:
                    continue
                
                # Solde EUR
                if asset == 'EUR':
                    total_value += total_balance
                    continue
                
                # Cryptomonnaies
                symbol = f"{asset}EUR"
                if symbol in symbols:
                    try:
                        ticker = self.api_client.safe_api_call(
                            self.api_client.client.get_symbol_ticker, 
                            symbol=symbol
                        )
                        if ticker:
                            price = float(ticker['price'])
                            asset_value = total_balance * price
                            total_value += asset_value
                            
                            # Log détaillé pour debug
                            if asset_value > 1.0:  # Seulement si significatif
                                console.print(f"   💰 {asset}: {total_balance:.4f} × {price:.2f}€ = {asset_value:.2f}€", style="dim")
                                
                    except Exception as e:
                        console.print(f"   ⚠️  Erreur prix {symbol}: {e}", style="yellow")
                        continue
            
            console.print(f"   📊 Valeur portefeuille: {total_value:.2f}€", style="bold green")
            return round(total_value, 2)
            
        except Exception as e:
            console.print(f"   ❌ Erreur calcul portefeuille: {e}", style="red")
            return 0.0
    
    def get_position_pnl(self, symbol, current_price):
        """Calcule le P&L d'une position"""
        if symbol not in self.entry_prices:
            return 0.0
        
        entry_price = self.entry_prices[symbol]
        if entry_price <= 0:
            return 0.0
        
        pnl_percent = ((current_price - entry_price) / entry_price) * 100
        return pnl_percent
    
    def add_position(self, symbol, entry_price):
        """Ajoute une nouvelle position"""
        self.entry_prices[symbol] = entry_price
        self.save_entry_prices()
        console.print(f"   ➕ Position ajoutée: {symbol} @ {entry_price:.2f}€", style="green")
    
    def remove_position(self, symbol):
        """Supprime une position"""
        if symbol in self.entry_prices:
            del self.entry_prices[symbol]
            self.save_entry_prices()
            console.print(f"   ➖ Position supprimée: {symbol}", style="yellow")
    
    def get_portfolio_summary(self, symbols_to_scan=None):
        """Retourne un résumé détaillé du portefeuille"""
        portfolio_value = self.update_portfolio_value(symbols_to_scan)
        positions_count = len(self.entry_prices)
        
        summary = {
            'total_value': portfolio_value,
            'positions_count': positions_count,
            'active_positions': list(self.entry_prices.keys()),
            'entry_prices': self.entry_prices.copy()
        }
        
        return summary
    
    def cleanup_unsellable_positions(self, api_client, symbols_to_scan):
        """Nettoie les positions qui ne peuvent pas être vendues (valeur < 1€)"""
        positions_to_remove = []
        
        for symbol in list(self.entry_prices.keys()):
            try:
                base_asset = symbol.replace('EUR', '')
                current_balance = api_client.get_current_balance(base_asset)
                
                if current_balance > 0:
                    current_price = api_client.get_current_price(symbol)
                    if current_price:
                        position_value = current_balance * current_price
                        if position_value < 1.0:  # Position invendable
                            positions_to_remove.append(symbol)
                            console.print(f"🧹 Nettoyage position invendable: {symbol} ({position_value:.2f}€)", style="yellow")
            except Exception as e:
                console.print(f"⚠️ Erreur vérification position {symbol}: {e}", style="yellow")
                continue
        
        # Supprimer les positions invendables
        for symbol in positions_to_remove:
            self.remove_position(symbol)
        
        return len(positions_to_remove)