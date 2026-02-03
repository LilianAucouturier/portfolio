# 🚀 Guide Setup - Next.js PWA "Cortex Run"

## Vue d'Ensemble

Ce guide vous accompagne pour initialiser le projet Next.js qui servira de Progressive Web App (PWA) installable sur iPhone.

**Stack** : Next.js 14 (App Router) + TypeScript + Tailwind CSS + Supabase

**Durée estimée** : 10-15 minutes

---

## PARTIE 1 : Création du Projet Next.js

### Étape 1.1 : Commande d'Initialisation

Ouvrez PowerShell dans le dossier `Cortex Run` et exécutez :

```powershell
npx create-next-app@latest . --typescript --tailwind --eslint --app --no-src --import-alias "@/*"
```

**Détail des options** :

- `.` → Installe dans le dossier actuel
- `--typescript` → Active TypeScript
- `--tailwind` → Configure Tailwind CSS automatiquement
- `--eslint` → Ajoute ESLint pour la qualité du code
- `--app` → Utilise le nouveau App Router (Next.js 14+)
- `--no-src` → Pas de dossier `/src` (structure simplifiée)
- `--import-alias "@/*"` → Imports absolus (ex: `import X from '@/components/X'`)

**Réponses aux prompts** (si demandé) :

- Would you like to use Turbopack? → **No** (stable uniquement)
- Initialize a git repository? → **Yes**

**Durée** : ~30 secondes (téléchargement des packages)

---

### Étape 1.2 : Vérifier la Structure

Après installation, vous devriez avoir :

```
Cortex Run/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── public/
├── node_modules/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
└── .eslintrc.json
```

---

## PARTIE 2 : Installation des Dépendances

### Étape 2.1 : Client Supabase

```powershell
npm install @supabase/supabase-js @supabase/ssr
```

**Packages installés** :

- `@supabase/supabase-js` → Client Supabase (requêtes DB, auth)
- `@supabase/ssr` → Helpers pour Server-Side Rendering (App Router)

---

### Étape 2.2 : Icônes Lucide React

```powershell
npm install lucide-react
```

**Usage** : Bibliothèque d'icônes moderne et légère (~300+ icônes)

---

### Étape 2.3 : Package PWA (next-pwa)

```powershell
npm install next-pwa
npm install --save-dev @types/serviceworker
```

**Packages** :

- `next-pwa` → Plugin pour générer Service Worker + manifest
- `@types/serviceworker` → Types TypeScript pour PWA

---

## PARTIE 3 : Configuration PWA

### Étape 3.1 : Créer le Manifest

Créez le fichier **`public/manifest.json`** :

```json
{
  "name": "Cortex Run - AI Running Coach",
  "short_name": "Cortex Run",
  "description": "Votre coach running personnel propulsé par l'IA",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0a0a0a",
  "theme_color": "#10b981",
  "orientation": "portrait",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "screenshots": [
    {
      "src": "/screenshot-mobile.png",
      "sizes": "390x844",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ],
  "categories": ["health", "sports", "lifestyle"],
  "shortcuts": [
    {
      "name": "Mon Programme",
      "url": "/program",
      "description": "Voir mon plan d'entraînement"
    },
    {
      "name": "Coach IA",
      "url": "/coach",
      "description": "Discuter avec le coach"
    }
  ]
}
```

**Remarques** :

- `display: standalone` → Enlève la barre d'URL Safari (app native)
- `theme_color: #10b981` → Vert émeraude (couleur running/santé)
- Les icônes 192x192 et 512x512 seront créées à l'étape suivante

---

### Étape 3.2 : Configuration next-pwa

Modifiez **`next.config.ts`** :

```typescript
import type { NextConfig } from "next";
import withPWA from "next-pwa";

const nextConfig: NextConfig = {
  reactStrictMode: true,
};

const config = withPWA({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development", // Désactivé en dev
  buildExcludes: [/middleware-manifest\.json$/],
})(nextConfig);

export default config;
```

---

### Étape 3.3 : Variables d'Environnement

Créez **`.env.local`** à la racine :

```env
NEXT_PUBLIC_SUPABASE_URL=https://VOTRE_PROJET.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbG...VOTRE_ANON_KEY
```

**⚠️ Remplacez** :

- `VOTRE_PROJET` → Votre URL Supabase
- `VOTRE_ANON_KEY` → Clé publique (anon)

**Sécurité** : Ajoutez `.env.local` au `.gitignore` (déjà fait par défaut)

---

## PARTIE 4 : Layout Mobile avec Bottom Navigation

### Étape 4.1 : Créer le Layout Racine

Remplacez **`app/layout.tsx`** par :

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import BottomNav from "@/components/BottomNav";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Cortex Run - AI Running Coach",
  description: "Votre coach running personnel propulsé par l'IA",
  manifest: "/manifest.json",
  themeColor: "#10b981",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Cortex Run",
  },
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <head>
        <link rel="apple-touch-icon" href="/icon-192.png" />
      </head>
      <body className={`${inter.className} bg-zinc-950 text-white`}>
        {/* Container avec padding bottom pour la nav */}
        <main className="min-h-screen pb-20">
          {children}
        </main>
        
        {/* Barre de navigation fixe en bas */}
        <BottomNav />
      </body>
    </html>
  );
}
```

**Points clés** :

- `appleWebApp.statusBarStyle: "black-translucent"` → Barre de statut iOS comme app native
- `pb-20` → Padding bottom pour ne pas cacher le contenu sous la nav
- `bg-zinc-950` → Fond noir (style moderne)

---

### Étape 4.2 : Créer le Composant BottomNav

Créez **`components/BottomNav.tsx`** :

```typescript
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Calendar, Bot, User } from "lucide-react";

const navItems = [
  { href: "/", icon: Home, label: "Accueil" },
  { href: "/program", icon: Calendar, label: "Programme" },
  { href: "/coach", icon: Bot, label: "Coach" },
  { href: "/profile", icon: User, label: "Profil" },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-zinc-900/95 backdrop-blur-lg border-t border-zinc-800 z-50">
      <div className="flex justify-around items-center h-16 px-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center w-full h-full transition-colors ${
                isActive
                  ? "text-emerald-500"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Icon size={24} strokeWidth={2} />
              <span className="text-xs mt-1 font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
```

**Fonctionnalités** :

- Détection de la route active avec `usePathname()`
- Effet de hover pour feedback visuel
- Icônes Lucide React (Home, Calendar, Bot, User)
- Glassmorphism : `bg-zinc-900/95 backdrop-blur-lg`

---

### Étape 4.3 : Page d'Accueil Temporaire

Remplacez **`app/page.tsx`** par :

```typescript
import { Activity, Heart, TrendingUp } from "lucide-react";

export default function Home() {
  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          Bonjour, Runner 🏃
        </h1>
        <p className="text-zinc-400">
          Prêt pour votre prochain entraînement ?
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard
          icon={<Activity size={20} />}
          label="Séances"
          value="12"
          trend="+2"
        />
        <StatCard
          icon={<Heart size={20} />}
          label="HRV"
          value="65ms"
          trend="+5%"
        />
        <StatCard
          icon={<TrendingUp size={20} />}
          label="Forme"
          value="8/10"
          trend="Bon"
        />
      </div>

      {/* Prochaine séance */}
      <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl p-6 mb-6">
        <p className="text-sm text-emerald-100 mb-2">Aujourd'hui</p>
        <h2 className="text-2xl font-bold mb-1">Endurance Facile</h2>
        <p className="text-emerald-100 mb-4">8 km · Zone 2 · 50 min</p>
        <button className="bg-white text-emerald-600 px-6 py-2 rounded-lg font-semibold">
          Démarrer
        </button>
      </div>

      {/* Placeholder sections */}
      <div className="space-y-4">
        <SectionPlaceholder title="Historique récent" />
        <SectionPlaceholder title="Objectif Marathon" />
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  trend,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  trend: string;
}) {
  return (
    <div className="bg-zinc-900 rounded-xl p-4">
      <div className="text-zinc-400 mb-2">{icon}</div>
      <div className="text-xs text-zinc-500 mb-1">{label}</div>
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs text-emerald-500">{trend}</div>
    </div>
  );
}

function SectionPlaceholder({ title }: { title: string }) {
  return (
    <div className="bg-zinc-900 rounded-xl p-6">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-zinc-500">À venir...</p>
    </div>
  );
}
```

---

### Étape 4.4 : Créer les Pages Placeholder

**`app/program/page.tsx`** :

```typescript
export default function ProgramPage() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">Mon Programme</h1>
      <p className="text-zinc-400">
        Votre plan d'entraînement personnalisé apparaîtra ici.
      </p>
    </div>
  );
}
```

**`app/coach/page.tsx`** :

```typescript
export default function CoachPage() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">Coach IA</h1>
      <p className="text-zinc-400">
        Interface de chat avec le coach IA.
      </p>
    </div>
  );
}
```

**`app/profile/page.tsx`** :

```typescript
export default function ProfilePage() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">Profil</h1>
      <p className="text-zinc-400">
        Paramètres et statistiques personnelles.
      </p>
    </div>
  );
}
```

---

## PARTIE 5 : Icônes PWA

### Étape 5.1 : Générer les Icônes

Vous pouvez :

**Option A - Temporaire** : Créer des icônes placeholder avec un générateur en ligne

- Allez sur [realfavicongenerator.net](https://realfavicongenerator.net)
- Uploadez un logo (ou texte "CR" pour Cortex Run)
- Téléchargez et placez dans `/public`

**Option B - Plus tard** : Créer un vrai logo avec un designer

**Fichiers requis** :

- `public/icon-192.png` (192x192px)
- `public/icon-512.png` (512x512px)
- `public/screenshot-mobile.png` (optionnel, pour App Store)

---

## PARTIE 6 : Tester le Projet

### Étape 6.1 : Lancer le Serveur de Développement

```powershell
npm run dev
```

**Accès** : Ouvrez [http://localhost:3000](http://localhost:3000)

**Vérifications** :

- ✅ Page d'accueil visible avec design noir/vert
- ✅ Bottom navigation fonctionnelle (4 onglets)
- ✅ Navigation entre les pages
- ✅ Responsive mobile (testez en mode mobile Chrome DevTools)

---

### Étape 6.2 : Tester la PWA (local)

1. **Ouvrez** Chrome DevTools (F12)
2. **Menu** → **Application** → **Manifest**
3. **Vérifiez** :
   - Name: "Cortex Run - AI Running Coach"
   - Display: standalone
   - Icons présents

---

## PARTIE 7 : Build de Production (Optionnel)

Pour tester la PWA installable (Service Worker uniquement en production) :

```powershell
npm run build
npm start
```

**Accès** : [http://localhost:3000](http://localhost:3000)

**Test d'installation** :

1. Ouvrez en mode mobile Chrome
2. Menu (3 points) → "Installer l'application"
3. L'app s'ouvre en mode standalone (sans barre d'URL)

---

## Résumé des Commandes

```powershell
# 1. Créer le projet
npx create-next-app@latest . --typescript --tailwind --eslint --app --no-src --import-alias "@/*"

# 2. Installer Supabase
npm install @supabase/supabase-js @supabase/ssr

# 3. Installer Lucide React
npm install lucide-react

# 4. Installer next-pwa
npm install next-pwa
npm install --save-dev @types/serviceworker

# 5. Lancer en dev
npm run dev
```

---

## Structure Finale

```
Cortex Run/
├── app/
│   ├── layout.tsx          ← Layout avec BottomNav
│   ├── page.tsx            ← Page d'accueil
│   ├── globals.css
│   ├── program/
│   │   └── page.tsx
│   ├── coach/
│   │   └── page.tsx
│   └── profile/
│       └── page.tsx
├── components/
│   └── BottomNav.tsx       ← Navigation bottom fixe
├── public/
│   ├── manifest.json       ← Config PWA
│   ├── icon-192.png
│   └── icon-512.png
├── .env.local              ← Clés Supabase
├── next.config.ts          ← Config PWA
└── package.json
```

---

## Prochaines Étapes

Une fois la coquille testée :

1. **Authentification Supabase** (login/signup)
2. **Lecture des métriques** (connexion à `daily_metrics`)
3. **Générateur de plan IA** (intégration Gemini)
4. **Interface Strava** (OAuth2 + sync activités)

---

**Besoin d'aide ?** Consultez la [documentation Next.js](https://nextjs.org/docs) ou [PWA Guide](https://web.dev/progressive-web-apps/)
