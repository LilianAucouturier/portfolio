#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de déploiement automatique Cortex Run (GitHub + Vercel)
Adapté de : Lilian Aucouturier
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def print_colored(message, color="cyan"):
    """Affiche un message avec une icône"""
    colors = {
        "cyan": "\033[96m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")


def run_git_command(command):
    """Exécute une commande git et retourne le résultat"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def main():
    # Chemin du projet Cortex Run
    project_path = Path(r"C:\Users\lilia\OneDrive - IPSA\Bureau\Cortex Run")
    
    print_colored("🚀 Démarrage du déploiement Cortex Run...", "cyan")
    
    current_path = Path.cwd()
    print(f"📂 Dossier actuel : {current_path}")
    
    # Déplacement automatique si nécessaire
    if current_path != project_path:
        print_colored(f"⚠️ Pas dans le bon dossier. Déplacement vers : {project_path}", "yellow")
        try:
            os.chdir(project_path)
            current_path = Path.cwd()
            print_colored(f"✅ Nouveau dossier : {current_path}", "green")
        except Exception as e:
            print_colored(f"❌ ERREUR : Impossible de se déplacer vers {project_path}", "red")
            print_colored(f"Détails : {e}", "red")
            input("Appuie sur Entrée pour quitter...")
            sys.exit(1)
    
    # Exécution du déploiement
    if current_path == project_path:
        print("📦 Préparation du colis (Git Add)...")
        success, output = run_git_command("git add .")
        if not success:
            print_colored(f"❌ Erreur lors du git add : {output}", "red")
            input("Appuie sur Entrée pour quitter...")
            sys.exit(1)
        
        # Date et Heure pour le commit
        date = datetime.now().strftime("%d/%m/%Y à %H:%M")
        
        print(f"🏷️ Étiquetage (Git Commit : {date})...")
        commit_message = f"Mise à jour Cortex Run du {date}"
        success, output = run_git_command(f'git commit -m "{commit_message}"')
        if not success:
            # Si pas de changements, ce n'est pas forcément une erreur
            if "nothing to commit" in output.lower():
                print_colored("ℹ️ Aucun changement à commiter", "yellow")
            else:
                print_colored(f"❌ Erreur lors du git commit : {output}", "red")
                input("Appuie sur Entrée pour quitter...")
                sys.exit(1)
        
        print("🚚 Envoi vers GitHub (Git Push)...")
        success, output = run_git_command("git push")
        if not success:
            print_colored(f"❌ Erreur lors du git push : {output}", "red")
            input("Appuie sur Entrée pour quitter...")
            sys.exit(1)
        
        print_colored("---------------------------------------------------", "green")
        print_colored("🎉 SUCCÈS ! Ton code est sur GitHub.", "green")
        print("⚡ Vercel est en train de construire la mise à jour.")
        print("👀 Suis le déploiement ici : https://vercel.com/dashboard")
        print_colored("---------------------------------------------------", "green")
        
        # Petite pause pour lire le message avant fermeture
        import time
        time.sleep(5)
    else:
        print_colored(f"❌ ERREUR : Impossible de trouver le dossier {project_path}", "red")
        input("Appuie sur Entrée pour quitter...")
        sys.exit(1)


if __name__ == "__main__":
    main()
