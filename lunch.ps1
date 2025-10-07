# --- Lunch.ps1 ---
# Script de publication automatique GitHub Pages
# Auteur : Lilian Aucouturier

# Chemin attendu du projet
$projectPath = "C:\Users\lilia\OneDrive - IPSA\Bureau\Portfolio"

Write-Host "Vérification du dossier courant..."
$currentPath = (Get-Location).Path
Write-Host "Dossier actuel : $currentPath"

# Si on n'est pas dans le bon dossier, on s'y déplace automatiquement
if ($currentPath -ne $projectPath) {
    Write-Host "Le dossier actuel n'est pas celui du projet."
    Write-Host "Déplacement automatique vers : $projectPath"
    Set-Location "$projectPath"
    $currentPath = (Get-Location).Path
    Write-Host "Nouveau dossier actuel : $currentPath"
}

# Double vérification pour éviter toute erreur
if ($currentPath -eq $projectPath) {
    Write-Host "Dossier correct. Début de la publication..."

    # Ajoute tous les fichiers modifiés
    git add .

    # Génère la date du jour
    $date = Get-Date -Format "dd/MM/yyyy"

    # Fait le commit avec la date
    git commit -m "Mise à jour du $date"

    # Push vers GitHub
    git push

    Write-Host "Publication terminée avec succès !"
    Write-Host "Consulte ton site ici : https://LilianAucouturier.github.io/portfolio"
} else {
    Write-Host "Impossible d'accéder au dossier projet. Vérifie le chemin manuellement."
}
