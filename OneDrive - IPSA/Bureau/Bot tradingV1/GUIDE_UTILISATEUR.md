# 📘 Guide Utilisateur - Bot Trading Crypto V1

Bienvenue dans le guide utilisateur de votre Bot de Trading Automatisé. Ce document vous explique comment installer, configurer et utiliser le bot via son tableau de bord interactif.

## 🚀 Installation

1. **Prérequis** :
    * Python 3.8 ou supérieur installé.
    * Un compte Binance (Testnet pour commencer).
    * Les clés API Binance (API Key et Secret Key).

2. **Installation des dépendances** :
    Ouvrez un terminal dans le dossier du projet et lancez :

    ```bash
    pip install -r requirements.txt
    ```

    *(Si `requirements.txt` n'existe pas, installez manuellement : `streamlit pandas ta python-binance plotly rich python-dotenv`)*

3. **Configuration de l'environnement** :
    Créez un fichier `.env` à la racine du projet avec vos clés :

    ```env
    BINANCE_API_KEY=votre_cle_api
    BINANCE_API_SECRET=votre_cle_secrete
    WHATSAPP_API_KEY=votre_cle_whatsapp (optionnel)
    WHATSAPP_PHONE=votre_numero (optionnel)
    ```

## 🎮 Démarrage

Pour lancer le bot et son interface de contrôle, exécutez simplement :

```bash
python main.py
```

Cela lancera automatiquement le Dashboard dans votre navigateur.

## 🖥️ Interface du Dashboard

### 1. Barre Latérale (Sidebar)

* **Contrôles du Bot** :
  * 🟢 **DÉMARRER LE BOT** : Lance le script de trading en arrière-plan.
  * 🔴 **ARRÊTER LE BOT** : Arrête proprement le processus de trading.
  * Le statut (ACTIF/ARRÊTÉ) et le PID sont affichés.
* **Configuration** :
  * Modifiez les paramètres en temps réel (Montant par trade, Stop Loss, Take Profit, Intervalle).
  * Cliquez sur **Sauvegarder** pour appliquer les changements immédiatement.
* **Performance Rapide** : Aperçu de la valeur du portefeuille et du P&L total.
* **Sentiment** : Affiche l'indice Fear & Greed et la tendance BTC.

### 2. Vue Principale

* **Évolution du Portefeuille** : Graphique historique de la valeur de votre compte.
* **Statistiques** : Win Rate, Ratio de Sharpe, Drawdown, Meilleur/Pire trade.
* **Analyse Technique** :
  * Sélectionnez une crypto dans la barre latérale.
  * Visualisez les graphiques 5min, 1h et 4h.
  * Indicateurs : RSI, MACD, Bandes de Bollinger, Moyennes Mobiles.
  * **Tendance 4H** : Analyse automatique de la tendance de fond.
* **Historique des Trades** : Liste des dernières opérations effectuées par le bot.
* **Analyse de Stratégie** : Statistiques sur l'efficacité de la stratégie (ex: Win Rate par zone RSI).

## 🧠 Fonctionnement du Bot

Le bot suit une stratégie "Multi-Timeframe" :

1. **Analyse de Tendance (4H)** : Il vérifie la tendance globale (Moyennes Mobiles 50/200). Il n'achète que si la tendance est favorable.
2. **Signaux d'Entrée (5min)** :
    * RSI en survente (<30).
    * Prix proche de la bande de Bollinger inférieure.
    * Confirmation par MACD ou Volume.
    * **NOUVEAU** : Prédiction ML (Machine Learning) simple pour confirmer la direction.
3. **Gestion de Position** :
    * Stop Loss (-5% par défaut).
    * Take Profit (+10% par défaut).
    * Sortie sur signal technique inverse (ex: RSI surachat).

## 🧪 Backtesting (Test sur le passé)

Pour tester la stratégie sur des données historiques (ex: 30 derniers jours) et générer un rapport de performance :

1. Ouvrez un terminal dans le dossier du bot.
2. Tapez la commande suivante :

   ```bash
   py backtester.py
   ```

   *(Note : Nous utilisons `py` pour assurer l'utilisation de la version récente de Python, car `python` par défaut est obsolète sur votre machine).*

3. Le bot va simuler les trades sur les 30 derniers jours pour BTCUSDT.
4. Un rapport complet sera généré : `rapport_backtest_BTCUSDT.html`.
5. Ouvrez ce fichier dans votre navigateur pour voir les courbes de performance et les trades détaillés.

## 6. Auto-Optimisation (Machine Learning)

Le bot peut "apprendre" de ses erreurs en testant des milliers de combinaisons de paramètres sur les données passées pour trouver les réglages les plus rentables.

1. **Lancer l'optimisation** :

   ```bash
   py optimizer.py
   ```

2. Le script va :
   * Télécharger l'historique récent.
   * Tester différentes valeurs de RSI (ex: acheter à 20, 25, 30... vendre à 70, 75, 80...).
   * Trouver la combinaison qui aurait généré le plus de profit.
   * Sauvegarder ces "meilleurs paramètres" dans `data/optimized_params.json`.

3. **Application** : Au prochain redémarrage, le bot utilisera automatiquement ces nouveaux paramètres optimisés au lieu des valeurs par défaut.

## ⚠️ Avertissements

* **Risques** : Le trading de crypto-monnaies comporte des risques élevés. N'investissez que ce que vous pouvez vous permettre de perdre.
* **Testnet** : Il est fortement recommandé de tester le bot sur le Testnet Binance avant de passer en réel.
* **Surveillance** : Bien que le bot soit automatisé, surveillez régulièrement ses performances via le dashboard.

---
*Développé avec ❤️ pour une expérience de trading optimale.*
