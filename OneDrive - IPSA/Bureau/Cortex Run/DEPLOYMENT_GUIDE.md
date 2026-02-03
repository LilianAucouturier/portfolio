# 🚀 Guide de Déploiement - Cortex Run

## Vue d'Ensemble

Ce guide vous accompagne pour mettre votre application en ligne (Production) afin de l'installer sur iPhone.

**Étapes** :

1. **GitHub** : Versionner votre code (le garage)
2. **Vercel** : Déployer en production (l'usine)
3. **Strava** : Mettre à jour le domaine d'autorisation

**Temps estimé** : 15-20 minutes

---

# PARTIE 1 : GITHUB (LE GARAGE) 📦

## Étape 1.1 : Initialiser Git

Ouvrez PowerShell dans votre dossier projet :

```powershell
cd "C:\Users\lilia\OneDrive - IPSA\Bureau\Cortex Run"
```

Initialisez git :

```powershell
git init
```

Vous devriez voir : `Initialized empty Git repository`

## Étape 1.2 : Créer .gitignore

Vérifiez que le fichier `.gitignore` existe. Si non, créez-le :

```gitignore
# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# local env files
.env*.local
.env

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts
```

**CRITIQUE** : `.env.local` ne doit **JAMAIS** être poussé sur GitHub (contient vos secrets).

## Étape 1.3 : Commit Initial

Ajoutez tous les fichiers :

```powershell
git add .
```

Committez :

```powershell
git commit -m "Initial commit - Cortex Run PWA"
```

## Étape 1.4 : Créer le Repo GitHub

**Sur le site GitHub** :

1. Allez sur <https://github.com>
2. Connectez-vous (ou créez un compte)
3. Cliquez sur le **+** en haut à droite
4. Sélectionnez **"New repository"**
5. Remplissez le formulaire :
   - **Repository name** : `cortex-run`
   - **Description** : "AI-powered running coach PWA"
   - **Visibility** : Public (ou Private si vous préférez)
   - **NE PAS** cocher "Add README" (vous en avez déjà un)
6. Cliquez **"Create repository"**

Vous arrivez sur une page avec des instructions. **Ignorez-les**, suivez les miennes.

## Étape 1.5 : Lier et Pousser

GitHub vous donne l'URL de votre repo. Elle ressemble à :

```
https://github.com/VOTRE_USERNAME/cortex-run.git
```

Dans PowerShell, ajoutez le remote :

```powershell
git remote add origin https://github.com/VOTRE_USERNAME/cortex-run.git
```

Renommez la branche en `main` (si elle s'appelle `master`) :

```powershell
git branch -M main
```

Poussez votre code :

```powershell
git push -u origin main
```

**Si demandé** : Entrez vos identifiants GitHub.

**Résultat** : Votre code est maintenant sur GitHub ! Rafraîchissez la page du repo pour le voir.

---

# PARTIE 2 : VERCEL (L'USINE) ⚡

## Étape 2.1 : Créer un Compte Vercel

1. Allez sur <https://vercel.com>
2. Cliquez **"Sign Up"**
3. Sélectionnez **"Continue with GitHub"**
4. Autorisez Vercel à accéder à votre compte GitHub

## Étape 2.2 : Importer le Projet

1. Une fois connecté, cliquez **"Add New"** → **"Project"**
2. Vous voyez la liste de vos repos GitHub
3. Trouvez **"cortex-run"**
4. Cliquez **"Import"**

## Étape 2.3 : Configurer le Projet

**Framework Preset** : Next.js (détecté automatiquement ✅)

**Root Directory** : `.` (garder par défaut)

**Build Command** : `npm run build` (par défaut, OK)

**Output Directory** : `.next` (par défaut, OK)

**NE PAS** cliquer "Deploy" tout de suite ! On doit d'abord configurer les variables d'environnement.

## Étape 2.4 : Environment Variables (CRITIQUE ⚠️)

Dans la section **"Environment Variables"**, ajoutez une par une :

### Variables OBLIGATOIRES

Copiez ces valeurs depuis votre `.env.local` :

| Key (Nom) | Value (Valeur) | Source |
|-----------|----------------|--------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://VOTRE_PROJET.supabase.co` | Dashboard Supabase → Project Settings → API |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbG...` (très long) | Dashboard Supabase → Project Settings → API → anon public |
| `GEMINI_API_KEY` | `AIzaSy...` | Google AI Studio |
| `STRAVA_CLIENT_ID` | `12345` | Strava API Settings |
| `STRAVA_CLIENT_SECRET` | `abc123...` | Strava API Settings |

### Variable SPÉCIALE (À METTRE À JOUR APRÈS)

| Key | Value TEMPORAIRE | Value FINALE |
|-----|------------------|--------------|
| `NEXT_PUBLIC_BASE_URL` | `https://cortex-run.vercel.app` | **À MODIFIER après déploiement** |

**Note** : Mettez une URL temporaire pour l'instant (ex: `https://cortex-run.vercel.app`). Vous la mettrez à jour à l'étape 2.6.

**Comment ajouter une variable** :

1. Tapez le `Key` (ex: `NEXT_PUBLIC_SUPABASE_URL`)
2. Tapez la `Value` (ex: `https://xyz.supabase.co`)
3. Cliquez **"Add"**
4. Répétez pour toutes les variables

## Étape 2.5 : Déployer

Cliquez **"Deploy"** (bouton bleu).

**Attendez** : Le build prend ~2-5 minutes.

Vous verrez :

- "Building..." (construction)
- "Deploying..." (déploiement)
- 🎉 **"Congratulations!"** (succès)

## Étape 2.6 : Récupérer l'URL de Production

Une fois déployé, Vercel vous donne l'URL :

```
https://cortex-run-abc123.vercel.app
```

**Copiez cette URL** (vous en aurez besoin pour Strava).

### Mettre à Jour NEXT_PUBLIC_BASE_URL

1. Sur Vercel, allez dans **"Settings"** (en haut)
2. Cliquez **"Environment Variables"** (menu gauche)
3. Trouvez `NEXT_PUBLIC_BASE_URL`
4. Cliquez sur les **3 points** → **"Edit"**
5. Remplacez par votre URL réelle : `https://cortex-run-abc123.vercel.app`
6. Cliquez **"Save"**
7. **Important** : Cliquez **"Redeploy"** (dans Deployments) pour appliquer le changement

---

# PARTIE 3 : STRAVA (LE DÉTAIL QUI TUE) 🏃

## Problème

Si vous essayez de connecter Strava maintenant, vous aurez :

```
ERROR: Invalid Redirect URI
```

**Pourquoi ?** Votre app Strava est configurée pour `localhost:3000`, pas votre domaine Vercel.

## Solution : Mettre à Jour le Domaine

### Étape 3.1 : Aller dans Strava API Settings

1. Allez sur <https://www.strava.com/settings/api>
2. Connectez-vous à Strava
3. Vous voyez votre application "Cortex Run" (ou le nom que vous avez donné)

### Étape 3.2 : Modifier l'Application

1. Cliquez sur **"Cortex Run"** (ou votre nom d'app)
2. Trouvez le champ **"Authorization Callback Domain"**

Actuellement, vous avez :

```
localhost:3000
```

### Étape 3.3 : Ajouter le Domaine Vercel

**IMPORTANT** : Vous pouvez avoir plusieurs domaines (séparés par des virgules).

Modifiez pour avoir :

```
localhost:3000, cortex-run-abc123.vercel.app
```

**Remplacez** `cortex-run-abc123.vercel.app` par **VOTRE** URL Vercel (sans `https://`).

**Pourquoi garder localhost ?** Pour continuer à développer en local.

### Étape 3.4 : Sauvegarder

Cliquez **"Update"** (en bas de la page).

**C'est fait !** 🎉

---

# PARTIE 4 : TESTER SUR IPHONE 📱

## Étape 4.1 : Ouvrir l'App sur iPhone

1. Sur votre iPhone, ouvrez **Safari**
2. Allez sur votre URL : `https://cortex-run-abc123.vercel.app`
3. L'app devrait charger (fond noir, barre de navigation en bas)

## Étape 4.2 : Installer la PWA

1. En bas au milieu, cliquez sur l'icône **"Partager"** (carré avec flèche)
2. Faites défiler → **"Sur l'écran d'accueil"**
3. Nommez l'app : "Cortex Run"
4. Cliquez **"Ajouter"**

**Résultat** : Une icône "Cortex Run" apparaît sur votre écran d'accueil comme une vraie app !

## Étape 4.3 : Tester Strava

1. Ouvrez l'app depuis l'écran d'accueil
2. Allez dans **"Profil"** (icône utilisateur en bas)
3. Cliquez **"Connecter Strava"**
4. Vous êtes redirigé vers Strava.com
5. Cliquez **"Authorize"**
6. **Vous revenez dans l'app** avec "✅ Strava connecté"

Si vous avez l'erreur "Invalid Redirect URI", **revérifiez** la Partie 3.

## Étape 4.4 : Synchroniser les Activités

1. Cliquez **"Synchroniser maintenant"**
2. Attendez 2-5 secondes
3. Message : "X nouvelle(s) course(s) synchronisée(s)"

**Bravo !** Votre app est en ligne et fonctionnelle. 🎉

---

# PARTIE 5 : MISES À JOUR FUTURES (BONUS) 🔄

## Quand Vous Modifiez le Code

1. **Commitez** vos changements :

   ```powershell
   git add .
   git commit -m "Description du changement"
   ```

2. **Poussez** sur GitHub :

   ```powershell
   git push
   ```

3. **Vercel déploie automatiquement** (en ~2 min)

**C'est tout !** Pas besoin de cliquer sur Vercel. Le déploiement automatique est activé par défaut.

## Voir les Déploiements

Sur Vercel Dashboard :

- Cliquez sur votre projet "cortex-run"
- Onglet **"Deployments"**
- Vous voyez l'historique (avec commit messages)

---

# TROUBLESHOOTING 🔧

## Problème : Build Failed sur Vercel

**Erreur** : "Command failed with exit code 1"

**Causes communes** :

1. **TypeScript errors** :
   - Vérifiez que `npm run build` marche en local
   - Corrigez les erreurs TypeScript avant de pousser

2. **Environment variables manquantes** :
   - Vérifiez que toutes les variables sont dans Vercel
   - Re-déployez après avoir ajouté une variable

3. **Import errors** :
   - Vérifiez les chemins d'import (`@/` doit être configuré dans `tsconfig.json`)

**Solution** :

1. Regardez les logs d'erreur dans Vercel (onglet "Deployments" → cliquez sur le build failed)
2. Corrigez l'erreur en local
3. Poussez à nouveau

## Problème : Les Variables d'Environnement ne Marchent Pas

**Symptôme** : "GEMINI_API_KEY is undefined"

**Solution** :

1. Vercel → Settings → Environment Variables
2. Vérifiez que la variable existe
3. **Redéployez** (les changements de variables nécessitent un redéploiement)

## Problème : Strava OAuth Ne Marche Pas

**Erreur** : "Invalid Redirect URI"

**Checklist** :

- ✅ `NEXT_PUBLIC_BASE_URL` dans Vercel = URL exacte (ex: `https://cortex-run.vercel.app`)
- ✅ Strava Authorization Domain = domaine Vercel (sans `https://`)
- ✅ Redéployé après avoir changé `NEXT_PUBLIC_BASE_URL`

## Problème : L'App Ne Se Charge Pas sur iPhone

**Symptôme** : Écran blanc ou erreur 500

**Causes** :

1. **Build failed** : Vérifiez sur Vercel Dashboard
2. **Variable manquante** : Vérifiez Supabase URL/Key
3. **Cache Safari** : Fermez Safari complètement et rouvrez

**Solution** :

- Mode développeur Safari : Settings → Safari → Advanced → Web Inspector
- Rechargez la page et regardez les erreurs Console

---

# RÉCAPITULATIF COMMANDES 📝

## GitHub (Une Fois)

```powershell
cd "C:\Users\lilia\OneDrive - IPSA\Bureau\Cortex Run"
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/VOTRE_USERNAME/cortex-run.git
git branch -M main
git push -u origin main
```

## Mises à Jour (Quotidien)

```powershell
git add .
git commit -m "Votre message"
git push
```

---

# CHECKLIST FINALE ✅

Avant de considérer le déploiement terminé :

- [ ] Code poussé sur GitHub
- [ ] Projet importé dans Vercel
- [ ] Toutes les variables d'env ajoutées
- [ ] `NEXT_PUBLIC_BASE_URL` mise à jour avec URL Vercel réelle
- [ ] Redéployé après changement de `BASE_URL`
- [ ] Strava Authorization Domain mis à jour
- [ ] App testée sur iPhone (chargement)
- [ ] PWA installée sur écran d'accueil
- [ ] Strava OAuth fonctionnel
- [ ] Sync activités réussie

**Si tous les points sont cochés : BRAVO ! 🎉**

Votre app est officiellement EN LIGNE et INSTALLABLE sur iPhone.

---

# PROCHAINES ÉTAPES 🚀

1. **Raccourci iOS** : Suivez `IOS_SHORTCUT_GUIDE.md` pour synchroniser vos métriques santé
2. **Générer un plan** : Allez dans Programme → "Générer mon plan IA"
3. **Suivre votre entraînement** : Marquez les séances comme complétées

Bon entraînement ! 🏃‍♂️💨
