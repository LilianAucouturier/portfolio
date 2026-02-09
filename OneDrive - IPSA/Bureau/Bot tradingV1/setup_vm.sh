#!/bin/bash

# setup_vm.sh - Script d'installation automatique pour Google Cloud (Ubuntu/Debian)

echo "🚀 Démarrage de l'installation..."

# 1. Mettre à jour le système
echo "📦 Mise à jour du système..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Installer Python 3, pip, git et screen
echo "🐍 Installation de Python et outils..."
sudo apt-get install -y python3 python3-pip python3-venv git screen

# 3. Créer le dossier du projet s'il n'existe pas
mkdir -p ~/trading-bot
cd ~/trading-bot

# 4. Cloner le repo (si le dossier est vide)
if [ ! -d ".git" ]; then
    echo "⬇️  Clonage du dépôt GitHub..."
    read -p "👉 Entrez l'URL de votre dépôt GitHub (ex: https://github.com/User/Repo.git) : " REPO_URL
    git clone $REPO_URL .
else
    echo "✅ Dépôt déjà présent, mise à jour..."
    git pull
fi

# 5. Créer l'environnement virtuel
echo "🔨 Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# 6. Installer les dépendances
echo "📚 Installation des librairies Python..."
pip install -r requirements.txt

echo "✅ Installation terminée !"
echo ""
echo "👉 Pour lancer le bot :"
echo "   1. Créez votre fichier .env : nano .env"
echo "   2. Collez vos clés API et sauvegardez (Ctrl+O, Entrée, Ctrl+X)"
echo "   3. Lancez le Dashboard dans un screen : screen -S dashboard"
echo "   4. Dans le screen : source venv/bin/activate && streamlit run dashboard.py --server.port=8080"
echo "   5. Détachez-vous du screen avec Ctrl+A puis D"
