# -*- coding: utf-8 -*-
# database.py - VERSION HYBRIDE (SQLite + PostgreSQL/Supabase)
import sqlite3
import pandas as pd
import os
import sys
import logging
from datetime import datetime

# Essayer d'importer psycopg2 pour PostgreSQL
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

# Logger pour Streamlit
logger = logging.getLogger(__name__)

class TradingDatabase:
    def __init__(self, db_path="data/trading.db"):
        self.db_path = db_path
        self.conn = None
        self.db_type = 'sqlite' # Par défaut
        self.connect()
        # On ne crée les tables automatiquement que si c'est SQLite
        # Pour Postgres, on suppose que le script SQL a été exécuté
        if self.db_type == 'sqlite':
            self.create_tables()

    def connect(self):
        """Établit la connexion (SQLite ou PostgreSQL selon ENV)"""
        database_url = os.getenv('DATABASE_URL')
        
        if database_url and HAS_POSTGRES:
            try:
                self.conn = psycopg2.connect(database_url)
                self.db_type = 'postgres'
                logger.info("SUCCESS - Connexion PostgreSQL (Supabase) établie")
            except Exception as e:
                logger.error(f"❌ Erreur connexion PostgreSQL: {e}")
                self.conn = None
        else:
            try:
                os.makedirs('data', exist_ok=True)
                self.conn = sqlite3.connect(self.db_path)
                self.conn.execute("PRAGMA foreign_keys = ON")
                self.db_type = 'sqlite'
                logger.info("SUCCESS - Connexion SQLite locale établie")
            except Exception as e:
                logger.error(f"❌ Erreur connexion SQLite: {e}")
                self.conn = None

    def _get_cursor(self):
        """Retourne un curseur adapté au type de DB"""
        if not self.conn:
            return None
        if self.db_type == 'postgres':
            return self.conn.cursor()
        return self.conn.cursor()

    def _execute(self, query, params=None):
        """Exécute une requête en adaptant la syntaxe des paramètres (? vs %s)"""
        if not self.conn:
            return None
            
        # Adaptation de la syntaxe des placeholders
        # SQLite utilise '?'
        # Psycopg2 utilise '%s'
        if self.db_type == 'postgres':
            query = query.replace('?', '%s')
            
        cursor = self._get_cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
        except Exception as e:
            logger.error(f"❌ Erreur SQL ({self.db_type}): {e}\nQuery: {query}")
            if self.conn:
                self.conn.rollback()
            return None
        """Crée les tables si elles n'existent pas"""
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            
            # Table des trades
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    entry_price REAL,
                    exit_price REAL,
                    quantity REAL,
                    pnl_percent REAL,
                    pnl_eur REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    strategy_version TEXT,
                    rsi_value REAL,
                    trend_4h TEXT
                )
            ''')

            # --- NOUVEAU: Table pour les trades virtuels (Simulation/Leaderboard) ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS virtual_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL, -- BUY, SELL
                    price REAL,
                    quantity REAL,
                    pnl_percent REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                )
            ''')
            
            # Table historique portefeuille
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_value REAL,
                    cash REAL,
                    crypto_value REAL,
                    positions_count INTEGER
                )
            ''')
            
            # Table des signaux (pour analyse)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    price REAL,
                    rsi REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    executed BOOLEAN DEFAULT FALSE,
                    reason TEXT
                )
            ''')
            
            # Table performance stratégie
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    strategy_name TEXT,
                    win_rate REAL,
                    total_trades INTEGER,
                    total_pnl REAL
                )
            ''')
            
            self.conn.commit()
            logger.info("SUCCESS -  Tables créées avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur création tables: {e}")
    
    def log_trade(self, symbol, action, entry_price, exit_price, quantity, 
                  pnl_percent=0, pnl_eur=0, reason="", strategy_version="v2.0",
                  rsi_value=None, trend_4h=None):
        """Enregistre un trade dans la base"""
        if not self.conn:
            return False
            
        try:
            # Les placeholders seront adaptés automatiquement par _execute
            self._execute('''
                INSERT INTO trades 
                (symbol, action, entry_price, exit_price, quantity, pnl_percent, 
                 pnl_eur, reason, strategy_version, rsi_value, trend_4h)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, action, entry_price, exit_price, quantity, pnl_percent, 
                  pnl_eur, reason, strategy_version, rsi_value, trend_4h))
            
            self.conn.commit()
            logger.info(f"SUCCESS -  Trade enregistré: {symbol} {action} | P&L: {pnl_percent:.2f}%")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur enregistrement trade: {e}")
            return False

    def log_virtual_trade(self, strategy_name, symbol, action, price, quantity, pnl_percent=0, reason=""):
        """Enregistre un trade vituel pour le leaderboard"""
        if not self.conn:
            return False
            
        try:
            self._execute('''
                INSERT INTO virtual_trades 
                (strategy_name, symbol, action, price, quantity, pnl_percent, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (strategy_name, symbol, action, price, quantity, pnl_percent, reason))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur enregistrement trade virtuel: {e}")
            return False
    
    def log_portfolio_snapshot(self, total_value, cash, crypto_value, positions_count):
        """Enregistre un snapshot du portefeuille"""
        if not self.conn:
            return False
            
        try:
            self._execute('''
                INSERT INTO portfolio_history 
                (total_value, cash, crypto_value, positions_count)
                VALUES (?, ?, ?, ?)
            ''', (total_value, cash, crypto_value, positions_count))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur snapshot portefeuille: {e}")
            return False
    
    def log_signal(self, symbol, signal, price, rsi, executed=False, reason=""):
        """Enregistre un signal de trading (même non exécuté)"""
        if not self.conn:
            return False
            
        try:
            self._execute('''
                INSERT INTO trading_signals 
                (symbol, signal, price, rsi, executed, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (symbol, signal, price, rsi, executed, reason))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur enregistrement signal: {e}")
            return False
    
    def get_trade_history(self, symbol=None, limit=100):
        """Récupère l'historique des trades"""
        if not self.conn:
            return pd.DataFrame()
            
        try:
            query = "SELECT * FROM trades"
            params = []
            
            if symbol:
                query += " WHERE symbol = ?"
                params.append(symbol)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            # Adaptation syntaxe pour pandas read_sql
            if self.db_type == 'postgres':
                query = query.replace('?', '%s')
            
            # Pour Pandas, on passe directement la connexion
            df = pd.read_sql_query(query, self.conn, params=params)
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération trades: {e}")
            return pd.DataFrame()
    
    def get_portfolio_history(self, days=30):
        """Récupère l'historique du portefeuille"""
        if not self.conn:
            return pd.DataFrame()
            
        try:
            # Gestion différence de syntaxe date
            if self.db_type == 'postgres':
                date_condition = f"timestamp >= NOW() - INTERVAL '{days} days'"
            else:
                date_condition = f"timestamp >= datetime('now', '-{days} days')"
                
            query = f"""
                SELECT * FROM portfolio_history 
                WHERE {date_condition}
                ORDER BY timestamp ASC
            """
            
            df = pd.read_sql_query(query, self.conn)
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération historique: {e}")
            return pd.DataFrame()
    
    def get_performance_stats(self, days=30):
        """Calcule les statistiques de performance"""
        if not self.conn:
            return {}
            
        try:
            # Gestion différence de syntaxe date
            if self.db_type == 'postgres':
                date_condition = f"timestamp >= NOW() - INTERVAL '{days} days'"
            else:
                date_condition = f"timestamp >= datetime('now', '-{days} days')"
            
            # --- Requête globale ---
            query = f"""
                SELECT 
                    COUNT(*) as total_trades,
                    AVG(pnl_percent) as avg_pnl_percent,
                    AVG(pnl_eur) as avg_pnl_eur,
                    SUM(CASE WHEN pnl_percent > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl_percent <= 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(pnl_eur) as total_pnl_eur
                FROM trades
                WHERE {date_condition}
            """
            cursor = self._execute(query)
            stats = cursor.fetchone()
            
            # --- Meilleur/Pire Trade ---
            query = f"""
                SELECT MAX(pnl_percent), MIN(pnl_percent) FROM trades
                WHERE {date_condition}
            """
            cursor = self._execute(query)
            best_worst = cursor.fetchone()
            
            # --- Performance par Symbole ---
            query = f"""
                SELECT symbol, COUNT(*), AVG(pnl_percent), SUM(pnl_eur)
                FROM trades 
                WHERE {date_condition}
                GROUP BY symbol
                ORDER BY SUM(pnl_eur) DESC
            """
            cursor = self._execute(query)
            by_symbol = cursor.fetchall()
            
            return {
                'total_trades': stats[0] or 0,
                'avg_pnl_percent': float(stats[1]) if stats[1] else 0,
                'avg_pnl_eur': float(stats[2]) if stats[2] else 0,
                'win_rate': (stats[3] / stats[0] * 100) if stats and stats[0] and stats[0] > 0 else 0,
                'best_trade': float(best_worst[0]) if best_worst[0] else 0,
                'worst_trade': float(best_worst[1]) if best_worst[1] else 0,
                'total_pnl_eur': float(stats[5]) if stats[5] else 0,
                'performance_by_symbol': [
                    {'symbol': row[0], 'trades': row[1], 'avg_pnl': row[2], 'total_pnl': row[3]}
                    for row in by_symbol
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur stats performance: {e}")
            return {}
            
    def get_strategy_leaderboard(self):
        """Récupère le classement des stratégies (Réelle vs Virtuelles)"""
        if not self.conn:
            return []
            
        try:
            leaderboard = []
            
            # 1. Stats de la stratégie RÉELLE (table trades)
            real_stats = self.get_performance_stats(days=365) # Tout l'historique
            leaderboard.append({
                'name': 'ACTUELLE (Réel)', 
                'type': 'REAL',
                'trades': real_stats.get('total_trades', 0),
                'win_rate': real_stats.get('win_rate', 0),
                'avg_pnl': real_stats.get('avg_pnl_percent', 0),
                'total_pnl': real_stats.get('total_pnl_eur', 0)
            })
            
            # 2. Stats des stratégies VIRTUELLES (table virtual_trades)
            query = '''
                SELECT 
                    strategy_name,
                    COUNT(*) as total_actions,
                    SUM(CASE WHEN action='SELL' THEN 1 ELSE 0 END) as finished_trades
                FROM virtual_trades
                GROUP BY strategy_name
            '''
            cursor = self._execute(query)
            strategies = cursor.fetchall()
            
            for strat in strategies:
                name = strat[0]
                
                # Calculer P&L moyen unique pour les ventes
                cursor = self._execute('''
                    SELECT AVG(pnl_percent), SUM(pnl_percent) 
                    FROM virtual_trades 
                    WHERE strategy_name = ? AND action = 'SELL'
                ''', (name,))
                pnl_data = cursor.fetchone()
                
                # Calculer Win Rate
                cursor = self._execute('''
                    SELECT COUNT(*) 
                    FROM virtual_trades 
                    WHERE strategy_name = ? AND action = 'SELL' AND pnl_percent > 0
                ''', (name,))
                wins = cursor.fetchone()[0]
                total_sells = strat[2]
                
                win_rate = (wins / total_sells * 100) if total_sells > 0 else 0
                avg_pnl = pnl_data[0] if pnl_data and pnl_data[0] else 0
                
                leaderboard.append({
                    'name': name,
                    'type': 'VIRTUAL',
                    'trades': total_sells,
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'total_pnl': pnl_data[1] if pnl_data and pnl_data[1] else 0
                })
                
            # Trier par P&L moyen
            leaderboard.sort(key=lambda x: x['avg_pnl'], reverse=True)
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"❌ Erreur classement stratégies: {e}")
            # En cas d'erreur de requête, on retourne ce qu'on a
            return leaderboard if leaderboard else []
    
    def get_strategy_analysis(self):
        """Analyse la performance de la stratégie"""
        if not self.conn:
            return {}
            
        try:
            # Performance par condition RSI
            cursor = self._execute('''
                SELECT 
                    CASE 
                        WHEN rsi_value < 30 THEN 'RSI < 30'
                        WHEN rsi_value > 70 THEN 'RSI > 70' 
                        ELSE 'RSI 30-70'
                    END as rsi_range,
                    COUNT(*) as trades,
                    AVG(pnl_percent) as avg_pnl,
                    SUM(CASE WHEN pnl_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
                FROM trades
                WHERE rsi_value IS NOT NULL
                GROUP BY rsi_range
            ''')
            rsi_performance = cursor.fetchall()
            
            # Performance par tendance
            cursor = self._execute('''
                SELECT 
                    trend_4h,
                    COUNT(*) as trades,
                    AVG(pnl_percent) as avg_pnl,
                    SUM(CASE WHEN pnl_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
                FROM trades
                WHERE trend_4h IS NOT NULL
                GROUP BY trend_4h
            ''')
            trend_performance = cursor.fetchall()
            
            return {
                'rsi_performance': [
                    {'range': row[0], 'trades': row[1], 'avg_pnl': row[2], 'win_rate': row[3]}
                    for row in rsi_performance
                ],
                'trend_performance': [
                    {'trend': row[0], 'trades': row[1], 'avg_pnl': row[2], 'win_rate': row[3]}
                    for row in trend_performance
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse stratégie: {e}")
            return {}
    
    def close(self):
        """Ferme la connexion"""
        if self.conn:
            self.conn.close()
            logger.info("SUCCESS -  Connexion DB fermée")

# Instance globale - SEULEMENT si exécuté directement
if __name__ == "__main__":
    db = TradingDatabase()