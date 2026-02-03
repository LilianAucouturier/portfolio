# 📱 Guide Complet - Raccourci iOS "Cortex Sync"

## Vue d'Ensemble

Ce guide vous accompagne pas à pas pour créer un raccourci iOS qui synchronise vos métriques Apple Health (Sommeil, HRV, Fréquence Cardiaque) vers votre base Supabase chaque matin.

**Durée estimée** : 15-20 minutes  
**Prérequis** :

- ✅ Apple Watch (pour HRV/FC Repos)
- ✅ iPhone avec iOS 14+
- ✅ App "Santé" configurée
- ✅ Backend Supabase opérationnel

---

## 🎯 Ce que fait le Raccourci

```mermaid
graph LR
    A[Tap Widget] --> B[Lit Apple Health]
    B --> C[Formate JSON]
    C --> D[Envoie à Supabase]
    D --> E[Notification Succès]
```

**Données synchronisées** :

- 🛌 Heures de sommeil
- ❤️ Variabilité cardiaque (HRV)
- 💓 Fréquence cardiaque au repos
- 🚶 Nombre de pas
- 🔥 Calories actives

---

## 📋 PARTIE 1 : Préparation

### Étape 1.1 : Récupérer votre User ID

1. **Ouvrez** Supabase Dashboard → **Authentication** → **Users**
2. **Cliquez** sur votre utilisateur test
3. **Copiez** le champ **UID** (format : `550e8400-e29b-41d4-a716-446655440000`)
4. **Collez** dans un fichier Notes (vous en aurez besoin)

### Étape 1.2 : Préparer vos Clés API

Ouvrez un fichier Notes et préparez ce template :

```json
{
  "user_id": "VOTRE_USER_ID_ICI",
  "date": "DATE_ACTUELLE",
  "sleep_duration_hours": SOMMEIL,
  "hrv_ms": HRV,
  "resting_hr": FC_REPOS,
  "steps": PAS,
  "active_calories": CALORIES
}
```

**Remplacez** `VOTRE_USER_ID_ICI` par l'UID copié à l'étape 1.1

**Gardez aussi à portée** :

- Votre **SUPABASE_URL** (ex: `https://abc123.supabase.co`)
- Votre **SERVICE_ROLE_KEY** (commence par `eyJhbG...`)

---

## 🔧 PARTIE 2 : Création du Raccourci

### Étape 2.1 : Ouvrir l'App Raccourcis

1. **Ouvrez** l'app **"Raccourcis"** (icône bleue avec carrés blancs)
2. **Tapez** le **+** en haut à droite
3. Vous êtes dans l'éditeur vide

---

### 🛌 Étape 2.2 : Récupérer le Sommeil

#### Action 1 : Rechercher "Analyse du sommeil"

1. **Tapez** dans la barre de recherche : `"santé"`
2. **Sélectionnez** : **"Rechercher des échantillons de santé"**
3. **Configurez** l'action :
   - **Type** : Tapez → `"Analyse du sommeil"`
   - **Trier par** : `"Date de début"`
   - **Ordre** : `"Le plus récent en premier"`
   - **Limite** : `1`
   - **Période** : `"Dernières 24 heures"`

> [!TIP]
> Cette action récupère votre dernière session de sommeil complète

#### Action 2 : Calculer la durée

1. **Recherchez** : `"obtenir les détails"`
2. **Sélectionnez** : **"Obtenir les détails des échantillons de santé"**
3. **Configurez** :
   - **Obtenir** : `"Durée"` (dans le menu déroulant)
   - **De** : `"Échantillons de santé"` (référence magique automatique)

#### Action 3 : Convertir en heures

1. **Recherchez** : `"calcul"`
2. **Sélectionnez** : **"Calculer"**
3. **Configurez** :
   - **Opération** : `"/"` (diviser)
   - **Premier nombre** : `"Durée"` (référence magique)
   - **Second nombre** : Tapez manuellement `3600` (secondes en 1 heure)

4. **Appuyez longtemps** sur l'action → **"Renommer"** → Tapez `"Heures Sommeil"`

---

### ❤️ Étape 2.3 : Récupérer la HRV

#### Action 4 : HRV

1. **Recherchez** : `"santé"`
2. **Sélectionnez** : **"Rechercher des échantillons de santé"**
3. **Configurez** :
   - **Type** : `"Variabilité de la fréquence cardiaque"`
   - **Trier par** : `"Date de début"`
   - **Ordre** : `"Le plus récent en premier"`
   - **Limite** : `1`
   - **Période** : `"Aujourd'hui"` (changez dans le menu)

#### Action 5 : Extraire la valeur HRV

1. **Recherchez** : `"obtenir les détails"`
2. **Sélectionnez** : **"Obtenir les détails des échantillons de santé"**
3. **Configurez** :
   - **Obtenir** : `"Valeur"` (dans le menu)
   - **De** : Automatique → Échantillons de santé HRV

4. **Renommez** : `"Valeur HRV"`

---

### 💓 Étape 2.4 : Récupérer la FC Repos

#### Action 6 : Fréquence cardiaque au repos

1. **Recherchez** : `"santé"`
2. **Sélectionnez** : **"Rechercher des échantillons de santé"**
3. **Configurez** :
   - **Type** : `"Fréquence cardiaque au repos"`
   - **Trier par** : `"Date de début"`
   - **Ordre** : `"Le plus récent en premier"`
   - **Limite** : `1`
   - **Période** : `"Aujourd'hui"`

#### Action 7 : Extraire la valeur

1. **Recherchez** : `"obtenir les détails"`
2. **Sélectionnez** : **"Obtenir les détails des échantillons de santé"**
3. **Configurez** :
   - **Obtenir** : `"Valeur"`
   - **De** : Automatique

4. **Renommez** : `"FC Repos"`

---

### 🚶 Étape 2.5 : Récupérer les Pas

#### Action 8 : Nombre de pas

1. **Recherchez** : `"santé"`
2. **Sélectionnez** : **"Rechercher des échantillons de santé"**
3. **Configurez** :
   - **Type** : `"Pas"`
   - **Trier par** : `"Date de début"`
   - **Ordre** : `"Le plus récent en premier"`
   - **Limite** : `1`
   - **Période** : `"Aujourd'hui"`

#### Action 9 : Extraire

1. **Obtenir les détails** → **Valeur**
2. **Renommez** : `"Pas"`

---

### 🔥 Étape 2.6 : Récupérer les Calories Actives

#### Action 10 : Calories actives

1. **Recherchez** : `"santé"`
2. **Sélectionnez** : **"Rechercher des échantillons de santé"**
3. **Configurez** :
   - **Type** : `"Énergie active"` ou `"Calories actives"`
   - **Trier par** : `"Date de début"`
   - **Ordre** : `"Le plus récent en premier"`
   - **Limite** : `1`
   - **Période** : `"Aujourd'hui"`

#### Action 11 : Extraire

1. **Obtenir les détails** → **Valeur**
2. **Renommez** : `"Calories"`

---

### 📅 Étape 2.7 : Obtenir la Date du Jour

#### Action 12 : Date actuelle

1. **Recherchez** : `"date actuelle"`
2. **Sélectionnez** : **"Date actuelle"**

#### Action 13 : Formater la date

1. **Recherchez** : `"formater la date"`
2. **Sélectionnez** : **"Formater la date"**
3. **Configurez** :
   - **Date** : `"Date actuelle"` (automatique)
   - **Format de date** : Tapez → `"Personnalisé"`
   - **Chaîne de format** : Tapez exactement `yyyy-MM-dd`

4. **Renommez** : `"Date Formatée"`

---

### 🔗 Étape 2.8 : Construire le JSON

> [!TIP]
> **Aperçu visuel** : Voici à quoi devrait ressembler votre action "Texte" avec les variables magiques :

![Configuration JSON avec variables magiques](C:/Users/lilia/.gemini/antigravity/brain/37f37881-9607-4671-a9be-fd03b0f43036/shortcut_json_example_1769700546757.png)

#### Action 14 : Texte avec le JSON

1. **Recherchez** : `"texte"`
2. **Sélectionnez** : **"Texte"**
3. **CRITIQUE** : Tapez EXACTEMENT ce JSON (remplacez `VOTRE_USER_ID`) :

```json
{
  "user_id": "VOTRE_USER_ID_ICI",
  "date": "Date Formatée",
  "sleep_duration_hours": Heures Sommeil,
  "hrv_ms": Valeur HRV,
  "resting_hr": FC Repos,
  "steps": Pas,
  "active_calories": Calories
}
```

**⚠️ ATTENTION : Étapes délicates**

1. **Remplacez** les valeurs colorées (variables magiques) :
   - Après `"date":`, **effacez** `"Date Formatée"`, puis :
     - **Tap** sur le champ
     - **Sélectionnez** `"Date Formatée"` dans le menu
   - Faites pareil pour :
     - `Heures Sommeil`
     - `Valeur HRV`
     - `FC Repos`
     - `Pas`
     - `Calories`

> [!IMPORTANT]
> Les variables doivent apparaître en **bleu/violet** (pas en texte noir). Si elles sont noires, ce sont juste des chaînes de texte !

1. **Renommez** l'action : `"Payload JSON"`

---

### 🌐 Étape 2.9 : Envoyer à Supabase

> [!TIP]
> **Aperçu visuel** : Configuration de la requête HTTP avec headers et body JSON :

![Configuration requête HTTP vers Supabase](C:/Users/lilia/.gemini/antigravity/brain/37f37881-9607-4671-a9be-fd03b0f43036/shortcut_http_headers_1769700572290.png)

#### Action 15 : Requête HTTP

1. **Recherchez** : `"URL"`
2. **Sélectionnez** : **"Obtenir le contenu d'une URL"**
3. **Configurez** :

**URL** :

```
https://VOTRE_PROJET.supabase.co/rest/v1/daily_metrics
```

(Remplacez `VOTRE_PROJET` par votre URL Supabase)

**Tapez** sur `"Afficher plus"` en bas de l'action

**Méthode** : `POST`

**En-têtes (Headers)** - **Ajoutez 4 en-têtes** :

| Clé | Valeur |
|-----|--------|
| `apikey` | `VOTRE_SERVICE_ROLE_KEY` |
| `Authorization` | `Bearer VOTRE_SERVICE_ROLE_KEY` |
| `Content-Type` | `application/json` |
| `Prefer` | `return=minimal` |

**Corps de la requête** :

- **Type** : `JSON`
- **Contenu** : Tapez sur le champ → Sélectionnez `"Payload JSON"` (variable magique bleue)

> [!WARNING]
> **SÉCURITÉ** : La `SERVICE_ROLE_KEY` sera stockée en clair dans le raccourci. Ne partagez JAMAIS ce raccourci par AirDrop.

---

### ✅ Étape 2.10 : Afficher la Confirmation

#### Action 16 : Vérifier le statut HTTP

1. **Recherchez** : `"si"`
2. **Sélectionnez** : **"Si"**
3. **Configurez** :
   - **Entrée** : Tapez `"Contenu de l'URL"` → Sélectionnez `"Code d'état"` (dans les variables magiques)
   - **Condition** : `"est"` (égal)
   - **Valeur** : `201`

#### Action 17 : Notification de succès

1. **Dans le bloc "Si"**, **recherchez** : `"notification"`
2. **Sélectionnez** : **"Afficher une notification"**
3. **Configurez** :
   - **Texte** : `✅ Métriques synchronisées !`

#### Action 18 : Notification d'erreur

1. **Après le "Si"**, **tap** sur `"Sinon"`
2. **Recherchez** : `"notification"`
3. **Sélectionnez** : **"Afficher une notification"**
4. **Configurez** :
   - **Texte** : `❌ Erreur de sync - Vérifiez votre connexion`

5. **Refermez** le bloc "Fin Si"

---

### 💾 Étape 2.11 : Sauvegarder le Raccourci

1. **Tapez** sur `"Terminé"` en haut à droite
2. **Nommez** le raccourci : `Cortex Sync`
3. **Tapez** sur le raccourci → `...` (3 points) → **"Détails"**
4. **Activez** :
   - ✅ **"Afficher dans le widget"**
   - ✅ **"Afficher sur l'écran d'accueil"**
5. **Choisissez** une icône (ex: ❤️ ou ⚡)

---

## 🧪 PARTIE 3 : Test du Raccourci

### Test 1 : Exécution Manuelle

1. **Ouvrez** l'app Raccourcis
2. **Tapez** sur `"Cortex Sync"`
3. **Autorisez** l'accès aux données Santé (popup iOS)
4. **Attendez** 2-5 secondes
5. **Vérifiez** la notification :
   - ✅ Si succès → Passez à l'étape Test 2
   - ❌ Si erreur → Consultez "Debugging" ci-dessous

### Test 2 : Vérification Base de Données

1. **Ouvrez** Supabase Dashboard
2. **Menu** → **Table Editor** → **`daily_metrics`**
3. **Vérifiez** qu'une nouvelle ligne apparaît avec :
   - ✅ `user_id` = Votre UUID
   - ✅ `date` = Date du jour (format `2026-01-29`)
   - ✅ `sleep_duration_hours` = valeur décimale (ex: `7.5`)
   - ✅ `hrv_ms` = entier (ex: `65`)
   - ✅ `resting_hr` = entier (ex: `52`)
   - ✅ `steps` = entier (ex: `8500`)

---

## 🐛 Debugging - Problèmes Fréquents

### ❌ Erreur : "Aucune donnée de santé trouvée"

**Causes possibles** :

- Apple Watch pas synchronisée
- Pas de données HRV aujourd'hui (portez la montre pendant le sommeil)
- App Santé non configurée

**Solution** :

1. Ouvrez **App Santé** → **Parcourir** → **Cœur** → **Variabilité**
2. Vérifiez qu'il y a des données récentes
3. Si vide → Portez l'Apple Watch cette nuit et réessayez demain

### ❌ Notification "Erreur de sync"

**Vérification 1 : URLs et Clés**

1. **Ouvrez** le raccourci en mode édition
2. **Vérifiez** l'action "Obtenir le contenu d'une URL" :
   - URL correcte ? (doit se terminer par `/rest/v1/daily_metrics`)
   - Header `apikey` renseigné ?
   - Header `Authorization` commence par `Bearer` ?

**Vérification 2 : Format JSON**

1. **Éditez** l'action "Texte" (le JSON)
2. **Vérifiez** que :
   - Les guillemets sont bien présents autour de `user_id` et `date`
   - **PAS** de guillemets autour des variables magiques bleues
   - Les virgules entre chaque ligne sont présentes

**Vérification 3 : Logs Supabase**

1. Supabase Dashboard → **Logs** → **API Logs**
2. Regardez la dernière requête POST sur `/daily_metrics`
3. Code d'erreur :
   - `401` → Problème d'authentification (clé API incorrecte)
   - `400` → JSON mal formaté
   - `409` → Doublon (vous avez déjà sync aujourd'hui)

### ❌ Valeurs NULL dans la base

**Cause** : Variable magique non liée correctement

**Solution** :

1. **Ouvrez** le raccourci en édition
2. **Pour chaque variable** dans le JSON :
   - Effacez la valeur
   - Re-tapez sur le champ
   - Re-sélectionnez la variable dans le menu
3. **Re-testez**

---

## 📲 PARTIE 4 : Automatisation Quotidienne

### Option A : Widget sur l'Écran d'Accueil

1. **Revenez** à l'écran d'accueil
2. **Appuyez longtemps** sur le fond d'écran → Mode Edition
3. **Tapez** le **+** en haut à gauche
4. **Recherchez** : `"Raccourcis"`
5. **Sélectionnez** le widget **1x1** ou **2x2**
6. **Tapez** sur `"Modifier le widget"`
7. **Choisissez** : `"Cortex Sync"`
8. **Placez** le widget en haut de votre écran

**Usage** : Chaque matin, 1 tap sur le widget = sync instantané

---

### Option B : Automatisation par Rappel

1. **Ouvrez** l'app **"Rappels"**
2. **Créez** un nouveau rappel :
   - Titre : `☀️ Sync Métriques Running`
   - Date : `Chaque jour`
   - Heure : `09:00` (après votre réveil habituel)
3. **Activez** la notification

**Workflow** :

- 9h00 → Notification rappel
- Vous tapez sur la notification
- Vous lancez manuellement `Cortex Sync` depuis le widget

> [!NOTE]
> iOS ne permet PAS l'exécution 100% automatique des raccourcis en arrière-plan. Une action utilisateur est toujours requise.

---

### Option C : Automatisation Focus (Avancé)

1. **App Raccourcis** → Onglet **"Automatisation"**
2. **Créer une automatisation personnelle**
3. **Déclencheur** : `"Heure"`
   - Quotidienne : 09:00
4. **Action** : `"Exécuter le raccourci"`
   - Choisir : `Cortex Sync`
5. **Désactiver** : `"Demander avant l'exécution"`

**⚠️ Limitation iOS** : L'automatisation affichera toujours une bannière de confirmation (impossible à supprimer sans Jailbreak).

---

## 📊 Exemple de Données Synchronisées

Voici ce que vous devriez voir dans Supabase après 1 semaine :

| date | sleep_duration_hours | hrv_ms | resting_hr | steps | active_calories |
|------|---------------------|--------|-----------|-------|----------------|
| 2026-01-29 | 7.5 | 65 | 52 | 8500 | 420 |
| 2026-01-30 | 6.8 | 58 | 54 | 12000 | 680 |
| 2026-01-31 | 8.2 | 72 | 51 | 5200 | 150 |
| 2026-02-01 | 7.0 | 61 | 53 | 9800 | 510 |

**Ces données seront utilisées par l'IA pour** :

- Détecter la fatigue (baisse HRV)
- Ajuster l'intensité des séances
- Recommander des jours de repos

---

## 🎯 Récapitulatif

Vous avez maintenant :

- ✅ Un raccourci fonctionnel qui lit Apple Health
- ✅ Synchronisation vers Supabase
- ✅ Widget sur l'écran d'accueil
- ✅ Notifications de succès/erreur

**Prochaine étape** : Développer l'interface Next.js pour visualiser ces données et générer votre plan d'entraînement IA 🏃‍♂️

---

## 📚 Ressources

- **Documentation Apple Shortcuts** : [support.apple.com/shortcuts](https://support.apple.com/guide/shortcuts/)
- **Supabase REST API** : [supabase.com/docs/guides/api](https://supabase.com/docs/guides/api)
- **Données Santé iOS** : [developer.apple.com/healthkit](https://developer.apple.com/documentation/healthkit)

---

**Besoin d'aide ?** Consultez la section Debugging ou contactez le support.
