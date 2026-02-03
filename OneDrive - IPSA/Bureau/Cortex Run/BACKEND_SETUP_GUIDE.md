# 🚀 Backend Setup - Guide Étape par Étape

## Vue d'Ensemble

Ce guide vous accompagne dans la configuration complète du backend Supabase pour votre PWA de coaching running.

**Durée estimée**: 10-15 minutes

---

## Étape 1: Créer un Projet Supabase

1. **Allez sur** [supabase.com](https://supabase.com)
2. **Cliquez** sur "Start your project"
3. **Connectez-vous** (GitHub recommended)
4. **Créez** un nouveau projet:
   - **Name**: `running-coach-ai` (ou votre choix)
   - **Database Password**: Générez un mot de passe fort (sauvegardez-le !)
   - **Region**: Europe West (Frankfurt) - plus proche de la France
   - **Pricing Plan**: Free
5. **Attendez** 1-2 minutes (création de la base de données)

---

## Étape 2: Exécuter le Script SQL

### 2.1 Ouvrir l'Éditeur SQL

1. Dans votre dashboard Supabase, **menu gauche** → **SQL Editor**
2. **Cliquez** sur "+ New query"

### 2.2 Copier-Coller le Script

1. **Ouvrez** le fichier [`supabase_init.sql`](file:///c:/Users/lilia/OneDrive%20-%20IPSA/Bureau/Cortex%20Run/supabase_init.sql)
2. **Sélectionnez tout** le contenu (Ctrl+A)
3. **Copiez** (Ctrl+C)
4. **Collez** dans l'éditeur SQL Supabase (Ctrl+V)

### 2.3 Exécuter

1. **Cliquez** sur le bouton "Run" (en bas à droite)
2. **Vérifiez** les messages de succès dans la console:

   ```
   ✅ Initialization complete!
   Tables created: 7
   RLS policies: Enabled
   ...
   ```

> [!TIP]
> Si erreur de syntaxe → vérifiez que TOUT le fichier a été copié (scroll jusqu'en bas)

---

## Étape 3: Vérifier la Structure

### 3.1 Vérifier les Tables

1. **Menu gauche** → **Table Editor**
2. Vous devriez voir **7 tables**:
   - ✅ `users`
   - ✅ `daily_metrics`
   - ✅ `activities`
   - ✅ `knowledge_docs`
   - ✅ `training_plans`
   - ✅ `training_sessions`
   - ✅ `ai_generations`

### 3.2 Vérifier les Seed Data

1. **Cliquez** sur la table `knowledge_docs`
2. Vous devriez voir **3 documents** insérés:
   - "Principes de Périodisation pour le 10km"
   - "Utilisation de la HRV pour Optimiser la Récupération"
   - "Structurer une Séance Intervalles VMA Efficace"

---

## Étape 4: Récupérer vos Clés API

### 4.1 Clés Nécessaires

1. **Menu gauche** → **Project Settings** (icône roue crantée)
2. **Cliquez** sur **API**
3. **Notez** ces informations:

| Clé | Usage | Où la noter |
|-----|-------|-------------|
| **Project URL** | URL de base API | Ex: `https://abc123.supabase.co` |
| **anon public** | Clé publique (frontend) | Utilisée dans Next.js |
| **service_role** | Clé secrète (backend) | Utilisée dans iOS Shortcut |

> [!WARNING]
> **NE JAMAIS** commiter la clé `service_role` dans Git ! Elle donne un accès total à votre DB.

### 4.2 Sauvegarde Sécurisée

Créez un fichier `.env.local` (à la racine de votre futur projet Next.js):

```env
NEXT_PUBLIC_SUPABASE_URL=https://VOTRE_PROJET.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbG...VOTRE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...VOTRE_SERVICE_KEY
```

---

## Étape 5: Tester l'Authentification

### 5.1 Créer un Utilisateur Test

1. **Menu gauche** → **Authentication** → **Users**
2. **Cliquez** sur "Add user" → "Create new user"
3. **Remplissez**:
   - Email: `test@runcoach.com`
   - Password: `TestPassword123!`
   - Auto Confirm User: ✅ (coché)
4. **Cliquez** "Create user"

### 5.2 Vérifier le Trigger

1. **Menu gauche** → **Table Editor** → **users**
2. Vous devriez voir **1 ligne** créée automatiquement avec:
   - `id` = UUID de l'utilisateur auth
   - `created_at` = Timestamp actuel
   - Autres colonnes = `NULL` (normal, seront remplies plus tard)

> [!IMPORTANT]
> Si la ligne n'apparaît PAS → le trigger `handle_new_user` a échoué. Vérifiez les logs dans **Database** → **Logs**.

---

## Étape 6: Tester l'API (Optionnel)

### 6.1 Test avec cURL

Ouvrez PowerShell et testez l'insertion de métriques quotidiennes:

```powershell
$headers = @{
    "apikey" = "VOTRE_SERVICE_ROLE_KEY"
    "Authorization" = "Bearer VOTRE_SERVICE_ROLE_KEY"
    "Content-Type" = "application/json"
}

$body = @{
    user_id = "UUID_DE_VOTRE_USER_TEST"
    date = "2026-01-29"
    sleep_duration_hours = 7.5
    hrv_ms = 65
    resting_hr = 52
    steps = 8500
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://VOTRE_PROJET.supabase.co/rest/v1/daily_metrics" `
    -Method Post `
    -Headers $headers `
    -Body $body
```

**Résultat attendu**: Status 201 Created

### 6.2 Vérifier dans la DB

1. **Table Editor** → **daily_metrics**
2. Une nouvelle ligne devrait apparaître

---

## Récapitulatif ✅

Vous avez maintenant:

- ✅ Un projet Supabase configuré
- ✅ 7 tables créées avec RLS activé
- ✅ Trigger d'authentification fonctionnel
- ✅ 3 documents de connaissance pour l'IA
- ✅ Vos clés API sauvegardées

---

## Prochaines Étapes

### Option A: Configuration du Shortcut iOS

→ Suivez le guide [`ios_shortcut_setup.md`](À créer)

### Option B: Développement Frontend (Next.js)

→ Initialisation du projet PWA (À documenter)

---

## Troubleshooting

### ❌ Erreur: "duplicate key value violates unique constraint"

**Cause**: Vous essayez de réexécuter le script  
**Solution**: Supprimez manuellement les tables dans **Database** → **Tables** avant de réexécuter

### ❌ Les policies RLS bloquent tout

**Cause**: Vous utilisez la clé `anon` au lieu de `service_role`  
**Solution**: Vérifiez que vous utilisez la bonne clé selon le contexte

### ❌ Le trigger ne crée pas l'utilisateur

**Cause**: Le trigger n'a pas été créé correctement  
**Solution**: Menu **Database** → **Functions** → vérifiez la présence de `handle_new_user`

---

**Besoin d'aide ?** Consultez la [documentation Supabase](https://supabase.com/docs)
