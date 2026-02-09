# main.py - Launcher du Bot Trading
import subprocess
import sys
import os
import time
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    """
    Point d'entrée principal.
    Lance le Dashboard Streamlit qui servira d'interface de contrôle.
    """
    console.print(Panel.fit("🚀 Lancement du Bot Trading...", style="bold blue"))
    
    # Vérifier l'environnement
    if not os.path.exists(".env"):
        console.print("⚠️ Fichier .env manquant !", style="yellow")
        console.print("Veuillez créer un fichier .env avec vos clés API.", style="yellow")
        input("Appuyez sur Entrée pour quitter...")
        return

    # Commande pour lancer Streamlit
    # On utilise sys.executable pour garantir l'utilisation du même environnement Python
    cmd = [sys.executable, "-m", "streamlit", "run", "dashboard.py"]
    
    # Configurer l'environnement pour UTF-8
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    console.print("📊 Démarrage de l'interface web...", style="green")
    console.print("👉 Si le navigateur ne s'ouvre pas, allez sur: http://localhost:8501")
    console.print("💡 Pour arrêter, faites Ctrl+C ici.", style="dim")
    
    try:
        # Lancement du processus
        process = subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        console.print("\n🛑 Arrêt du launcher.", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Erreur: {e}", style="red")

if __name__ == "__main__":
    main()