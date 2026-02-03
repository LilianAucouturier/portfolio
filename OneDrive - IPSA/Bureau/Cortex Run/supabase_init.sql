-- ============================================
-- RUNNING COACH PWA - SUPABASE INITIALIZATION
-- ============================================
-- Version: 1.0
-- Date: 2026-01-29
-- Description: Complete database setup for AI-powered running coach
-- 
-- USAGE:
--   1. Open your Supabase project dashboard
--   2. Go to SQL Editor
--   3. Copy-paste this entire file
--   4. Execute (Run)
-- ============================================

-- ============================================
-- PART 1: TABLES CREATION
-- ============================================

-- --------------------------------------------
-- TABLE: users (extension of auth.users)
-- Profil athlète et paramètres d'entraînement
-- --------------------------------------------
CREATE TABLE public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Profil personnel
  name TEXT,
  birth_date DATE,
  weight_kg DECIMAL(5,2),
  
  -- Fréquences cardiaques
  max_hr INTEGER CHECK (max_hr > 0 AND max_hr <= 220),
  rest_hr INTEGER CHECK (rest_hr > 0 AND rest_hr < 100),
  
  -- Objectifs
  goal_type TEXT CHECK (goal_type IN ('5k', '10k', 'half_marathon', 'marathon', 'ultra', 'fitness')),
  goal_date DATE,
  current_weekly_volume_km DECIMAL(5,2) CHECK (current_weekly_volume_km >= 0),
  experience_level TEXT CHECK (experience_level IN ('beginner', 'intermediate', 'advanced', 'elite')),
  
  -- Intégrations externes
  strava_access_token TEXT,
  strava_refresh_token TEXT,
  strava_expires_at TIMESTAMPTZ,
  strava_athlete_id BIGINT
);

COMMENT ON TABLE public.users IS 'Profils athlètes et configuration personnelle';

-- --------------------------------------------
-- TABLE: daily_metrics
-- Métriques Apple Health (via iOS Shortcut)
-- --------------------------------------------
CREATE TABLE public.daily_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Sommeil
  sleep_duration_hours DECIMAL(4,2) CHECK (sleep_duration_hours >= 0 AND sleep_duration_hours <= 24),
  sleep_quality_score INTEGER CHECK (sleep_quality_score BETWEEN 0 AND 100),
  
  -- Variabilité cardiaque et fréquence
  hrv_ms INTEGER CHECK (hrv_ms > 0 AND hrv_ms < 300),
  resting_hr INTEGER CHECK (resting_hr > 0 AND resting_hr < 150),
  
  -- Activité générale
  steps INTEGER CHECK (steps >= 0),
  active_calories INTEGER CHECK (active_calories >= 0),
  
  -- Évaluation subjective (renseigné manuellement via app)
  fatigue_score INTEGER CHECK (fatigue_score BETWEEN 1 AND 10),
  muscle_soreness INTEGER CHECK (muscle_soreness BETWEEN 1 AND 10),
  mood_score INTEGER CHECK (mood_score BETWEEN 1 AND 10),
  
  -- Métadonnées
  notes TEXT,
  
  UNIQUE(user_id, date)
);

COMMENT ON TABLE public.daily_metrics IS 'Métriques quotidiennes de santé (Apple Health + saisie manuelle)';
COMMENT ON COLUMN public.daily_metrics.fatigue_score IS '1=épuisé, 10=forme olympique';
COMMENT ON COLUMN public.daily_metrics.muscle_soreness IS '1=aucune douleur, 10=courbatures sévères';

CREATE INDEX idx_daily_metrics_user_date ON public.daily_metrics(user_id, date DESC);

-- --------------------------------------------
-- TABLE: activities
-- Activités sportives (Strava sync)
-- --------------------------------------------
CREATE TABLE public.activities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  strava_id BIGINT UNIQUE,
  
  activity_date TIMESTAMPTZ NOT NULL,
  activity_type TEXT NOT NULL CHECK (activity_type IN ('run', 'trail_run', 'race', 'walk', 'other')),
  
  -- Métriques brutes
  distance_km DECIMAL(6,2) CHECK (distance_km > 0),
  duration_seconds INTEGER CHECK (duration_seconds > 0),
  elevation_gain_m INTEGER CHECK (elevation_gain_m >= 0),
  average_hr INTEGER CHECK (average_hr > 0 AND average_hr <= 220),
  max_hr INTEGER CHECK (max_hr > 0 AND max_hr <= 220),
  
  -- Métriques calculées
  pace_min_per_km DECIMAL(4,2) GENERATED ALWAYS AS (
    CASE 
      WHEN distance_km > 0 THEN (duration_seconds / 60.0) / distance_km
      ELSE NULL
    END
  ) STORED,
  
  -- Zone d'effort (1-5)
  effort_zone INTEGER CHECK (effort_zone BETWEEN 1 AND 5),
  
  -- Perception de l'effort (RPE: Rate of Perceived Exertion)
  rpe_score INTEGER CHECK (rpe_score BETWEEN 1 AND 10),
  
  -- Données brutes Strava (backup JSON)
  raw_data JSONB,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.activities IS 'Activités sportives synchronisées depuis Strava';
COMMENT ON COLUMN public.activities.effort_zone IS 'Zone FC calculée: 1=récup, 2=endurance, 3=tempo, 4=seuil, 5=VMA';
COMMENT ON COLUMN public.activities.rpe_score IS 'Rate of Perceived Exertion (1=très facile, 10=maximal)';

CREATE INDEX idx_activities_user_date ON public.activities(user_id, activity_date DESC);
CREATE INDEX idx_activities_strava_id ON public.activities(strava_id) WHERE strava_id IS NOT NULL;

-- --------------------------------------------
-- TABLE: knowledge_docs
-- Base de connaissances scientifiques
-- --------------------------------------------
CREATE TABLE public.knowledge_docs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  title TEXT NOT NULL,
  source TEXT,
  doc_type TEXT CHECK (doc_type IN ('pdf', 'article', 'study', 'book', 'blog')),
  
  -- Contenu (texte brut extrait)
  content TEXT NOT NULL,
  
  -- Métadonnées pour filtrage contextuel
  topics TEXT[] DEFAULT '{}',
  target_audience TEXT[] DEFAULT '{}',
  language TEXT DEFAULT 'fr',
  
  -- Recherche full-text
  content_search TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('french', coalesce(title, '') || ' ' || coalesce(content, ''))
  ) STORED
);

COMMENT ON TABLE public.knowledge_docs IS 'Base de connaissances pour IA (PDFs, articles scientifiques)';
COMMENT ON COLUMN public.knowledge_docs.topics IS 'Tags: periodization, vo2max, injury_prevention, nutrition, etc.';
COMMENT ON COLUMN public.knowledge_docs.target_audience IS 'Niveaux: beginner, intermediate, advanced, elite';

CREATE INDEX idx_knowledge_search ON public.knowledge_docs USING GIN(content_search);
CREATE INDEX idx_knowledge_topics ON public.knowledge_docs USING GIN(topics);

-- --------------------------------------------
-- TABLE: training_plans
-- Plans d'entraînement générés par IA
-- --------------------------------------------
CREATE TABLE public.training_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  start_date DATE NOT NULL,
  end_date DATE,
  
  status TEXT DEFAULT 'active' CHECK (status IN ('draft', 'active', 'completed', 'archived')),
  
  -- Contexte de génération (traçabilité)
  generation_context JSONB,
  
  -- Philosophie du plan (texte explicatif de l'IA)
  coaching_philosophy TEXT,
  
  -- Métadonnées
  total_weeks INTEGER CHECK (total_weeks > 0),
  target_race_date DATE,
  target_race_distance TEXT
);

COMMENT ON TABLE public.training_plans IS 'Plans dentraînement générés par Gemini AI';
COMMENT ON COLUMN public.training_plans.generation_context IS 'Données ayant influencé la génération: {avg_hrv_7d, fatigue_trend, recent_volume, etc.}';

CREATE INDEX idx_training_plans_user_status ON public.training_plans(user_id, status, start_date DESC);

-- --------------------------------------------
-- TABLE: training_sessions
-- Séances individuelles du plan
-- --------------------------------------------
CREATE TABLE public.training_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID NOT NULL REFERENCES public.training_plans(id) ON DELETE CASCADE,
  
  date DATE NOT NULL,
  week_number INTEGER NOT NULL CHECK (week_number > 0),
  
  -- Type de séance
  session_type TEXT NOT NULL CHECK (
    session_type IN ('endurance', 'tempo', 'intervals', 'long_run', 'recovery', 'rest', 'race')
  ),
  
  -- Prescription
  target_distance_km DECIMAL(5,2) CHECK (target_distance_km >= 0),
  target_duration_minutes INTEGER CHECK (target_duration_minutes > 0),
  target_pace_range TEXT,
  target_hr_zone INTEGER CHECK (target_hr_zone BETWEEN 1 AND 5),
  
  -- Structure détaillée (JSON)
  workout_structure JSONB,
  
  -- Raison pédagogique (expliqué par l'IA)
  rationale TEXT,
  
  -- Statut d'exécution
  completed BOOLEAN DEFAULT FALSE,
  completed_at TIMESTAMPTZ,
  completed_activity_id UUID REFERENCES public.activities(id) ON DELETE SET NULL,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.training_sessions IS 'Séances individuelles constituant les plans dentraînement';
COMMENT ON COLUMN public.training_sessions.workout_structure IS 'Format: {warmup: {duration: 15}, main: [...], cooldown: {duration: 10}}';

CREATE INDEX idx_sessions_plan_date ON public.training_sessions(plan_id, date);
CREATE INDEX idx_sessions_completion ON public.training_sessions(plan_id, completed, date);

-- --------------------------------------------
-- TABLE: ai_generations
-- Logs des requêtes IA (monitoring quotas)
-- --------------------------------------------
CREATE TABLE public.ai_generations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  generation_type TEXT NOT NULL CHECK (
    generation_type IN ('training_plan', 'session_adjustment', 'advice', 'analysis')
  ),
  
  -- Prompt envoyé
  prompt_template TEXT,
  prompt_context JSONB,
  
  -- Réponse brute
  raw_response TEXT,
  response_status TEXT DEFAULT 'success' CHECK (response_status IN ('success', 'error', 'timeout')),
  
  -- Monitoring
  tokens_used INTEGER CHECK (tokens_used >= 0),
  latency_ms INTEGER,
  
  -- Résultat parsé (si applicable)
  parsed_output JSONB,
  
  error_message TEXT
);

COMMENT ON TABLE public.ai_generations IS 'Logs de toutes les générations IA (debug + monitoring quotas Gemini)';

CREATE INDEX idx_ai_generations_user_date ON public.ai_generations(user_id, created_at DESC);
CREATE INDEX idx_ai_generations_type ON public.ai_generations(generation_type, created_at DESC);

-- ============================================
-- PART 2: ROW LEVEL SECURITY (RLS)
-- ============================================

-- Activer RLS sur toutes les tables sensibles
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.training_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.training_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_generations ENABLE ROW LEVEL SECURITY;

-- Note: knowledge_docs est PUBLIC (pas de RLS, accessible par tous)

-- --------------------------------------------
-- Policies: USERS
-- --------------------------------------------
CREATE POLICY "Users can view own profile" 
  ON public.users FOR SELECT 
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
  ON public.users FOR UPDATE 
  USING (auth.uid() = id);

-- --------------------------------------------
-- Policies: DAILY_METRICS
-- --------------------------------------------
CREATE POLICY "Users can view own daily metrics" 
  ON public.daily_metrics FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own daily metrics" 
  ON public.daily_metrics FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own daily metrics" 
  ON public.daily_metrics FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own daily metrics" 
  ON public.daily_metrics FOR DELETE 
  USING (auth.uid() = user_id);

-- Policy spéciale: Permettre insertion via Service Role (pour iOS Shortcut)
-- Note: Cette policy sera utilisée quand le Shortcut envoie avec la Service Key
CREATE POLICY "Service role can insert metrics for any user" 
  ON public.daily_metrics FOR INSERT 
  WITH CHECK (
    current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
  );

-- --------------------------------------------
-- Policies: ACTIVITIES
-- --------------------------------------------
CREATE POLICY "Users can manage own activities" 
  ON public.activities FOR ALL 
  USING (auth.uid() = user_id);

-- --------------------------------------------
-- Policies: TRAINING_PLANS
-- --------------------------------------------
CREATE POLICY "Users can manage own training plans" 
  ON public.training_plans FOR ALL 
  USING (auth.uid() = user_id);

-- --------------------------------------------
-- Policies: TRAINING_SESSIONS
-- --------------------------------------------
-- Les sessions sont accessibles via le plan_id (jointure implicite)
CREATE POLICY "Users can manage sessions of own plans" 
  ON public.training_sessions FOR ALL 
  USING (
    EXISTS (
      SELECT 1 FROM public.training_plans 
      WHERE training_plans.id = training_sessions.plan_id 
      AND training_plans.user_id = auth.uid()
    )
  );

-- --------------------------------------------
-- Policies: AI_GENERATIONS
-- --------------------------------------------
CREATE POLICY "Users can view own AI generations" 
  ON public.ai_generations FOR SELECT 
  USING (auth.uid() = user_id);

-- Les insertions se font côté serveur (Edge Functions)
CREATE POLICY "Service role can insert AI generations" 
  ON public.ai_generations FOR INSERT 
  WITH CHECK (
    current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
  );

-- ============================================
-- PART 3: TRIGGERS & FUNCTIONS
-- ============================================

-- --------------------------------------------
-- Function: Auto-create user profile on signup
-- --------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, created_at)
  VALUES (NEW.id, NOW());
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.handle_new_user IS 'Crée automatiquement un profil dans public.users quand un utilisateur sinscrit via Supabase Auth';

-- Trigger sur auth.users (table système Supabase)
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- --------------------------------------------
-- Function: Update timestamp automatique
-- --------------------------------------------
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Appliquer sur les tables avec updated_at
CREATE TRIGGER set_updated_at_users
  BEFORE UPDATE ON public.users
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER set_updated_at_training_plans
  BEFORE UPDATE ON public.training_plans
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at();

-- ============================================
-- PART 4: SEED DATA (Knowledge Docs)
-- ============================================

-- Document 1: Principes de la périodisation
INSERT INTO public.knowledge_docs (
  title,
  source,
  doc_type,
  content,
  topics,
  target_audience,
  language
) VALUES (
  'Principes de Périodisation pour le 10km',
  'Science of Running - Steve Magness (adapté)',
  'article',
  E'# Périodisation pour le 10km\n\n## Introduction\n\nLa périodisation est le processus de division de lentraînement en phases distinctes pour optimiser la performance. Pour un objectif 10km, un plan typique sétend sur 8-12 semaines.\n\n## Les 3 Phases Clés\n\n### Phase 1: Base Endurance (3-4 semaines)\n- **Objectif**: Construire une base aérobie solide\n- **Volume**: 70-80% de course facile (Zone 2: 65-75% FCmax)\n- **Fréquence**: 4-5 sorties/semaine\n- **Principe scientifique**: Développement mitochondrial et capillarisation musculaire\n\n### Phase 2: Développement Seuil (3-4 semaines)\n- **Objectif**: Augmenter le seuil lactique (tempo runs)\n- **Séances clés**: \n  * 1x tempo run (20-30min à 80-85% FCmax)\n  * 1x long run progressif\n  * 2-3x endurance facile\n- **Principe scientifique**: Amélioration de la capacité à tolérer le lactate\n\n### Phase 3: Affûtage VMA (2-3 semaines)\n- **Objectif**: Maximiser la VO2max et la vitesse spécifique 10km\n- **Séances clés**:\n  * Intervalles 5x1000m @ allure 5km avec 2min récup\n  * Tempo run court (15min @ allure 10km)\n  * Réduction progressive du volume (-20% par semaine)\n- **Principe scientifique**: Supercompensation avant la course\n\n## Règles de Progression\n\n1. **Règle des 10%**: Naugmentez jamais le volume hebdomadaire de plus de 10%\n2. **Hard/Easy**: Alternez jours difficiles et jours faciles\n3. **Récupération**: Intégrez 1-2 jours de repos complet/semaine\n\n## Exemple de Semaine Type (Phase 2)\n\n- **Lundi**: Repos ou cross-training léger\n- **Mardi**: 8km endurance (Zone 2) + 6x100m strides\n- **Mercredi**: 10km avec 20min tempo (Zone 3-4)\n- **Jeudi**: Repos ou 5km récupération\n- **Vendredi**: 8km endurance facile\n- **Samedi**: Intervalles 6x800m @ allure 5km (récup 90s)\n- **Dimanche**: Long run 14-16km progressif\n\n## Adaptation selon les Signaux de Fatigue\n\n**Si HRV baisse > 10%** → Reporter la séance intense, remplacer par endurance facile\n**Si sommeil < 7h pendant 3 jours** → Semaine de récupération forcée\n**Si douleurs musculaires persistantes** → Jour de repos supplémentaire\n\n## Références\n\n- Lydiard, Arthur. "Running to the Top" (1997)\n- Daniels, Jack. "Daniels Running Formula" (2013)\n- Magness, Steve. "The Science of Running" (2014)',
  ARRAY['periodization', '10k', 'training_phases', 'tempo', 'intervals'],
  ARRAY['intermediate', 'advanced'],
  'fr'
);

-- Document 2: Gestion de la récupération via HRV
INSERT INTO public.knowledge_docs (
  title,
  source,
  doc_type,
  content,
  topics,
  target_audience,
  language
) VALUES (
  'Utilisation de la HRV pour Optimiser la Récupération',
  'Journal of Sports Science, 2019',
  'study',
  E'# HRV (Heart Rate Variability) et Entraînement\n\n## Quest-ce que la HRV ?\n\nLa variabilité de la fréquence cardiaque (HRV) mesure la variation de temps entre chaque battement de cœur. Une **HRV élevée** indique un système nerveux parasympathique dominant (récupération), tandis quune **HRV basse** suggère stress/fatigue.\n\n## Valeurs de Référence\n\n- **Athlète bien récupéré**: 60-100 ms (varie selon lindividu)\n- **Fatigue modérée**: -10 à -20% de la baseline personnelle\n- **Surcharge importante**: -20% ou plus\n\n## Protocole dUtilisation\n\n### 1. Établir sa Baseline\nMesurer la HRV **chaque matin** pendant 2 semaines (au repos, au réveil).\nCalculer la **moyenne des 7 derniers jours** = Baseline personnelle.\n\n### 2. Règle de Décision\n\n| HRV du jour vs Baseline | Action Recommandée |\n|------------------------|--------------------|\n| > +5%                  | Journée intense possible (intervalles, tempo) |\n| ±5%                    | Entraînement normal selon plan |\n| -10% à -15%            | Remplacer séance intense par endurance facile |\n| < -15%                 | Repos complet ou récupération active légère |\n\n### 3. Exemple Concret\n\n**Situation**: Plan prévoit 10x400m mardi. HRV mesurée = 45ms (baseline = 65ms → -31%)\n\n**Décision IA**:\n- ❌ Annuler les intervalles\n- ✅ Proposer 30min course facile Zone 1-2\n- ✅ Reporter les intervalles à jeudi (si HRV remonte)\n\n## Intégration dans lAlgorithme dAjustement\n\n```pseudocode\nIF avg_hrv_7d < (baseline * 0.85) THEN\n  → Semaine de récupération forcée\n  → Volume -30%\n  → Aucune séance haute intensité\nELSE IF hrv_today < (baseline * 0.90) THEN\n  → Ajuster séance du jour uniquement\nEND IF\n```\n\n## Limitations\n\n- La HRV nest pas le seul indicateur (combiner avec sommeil, fatigue subjective)\n- Variabilité inter-individuelle importante (pas de valeur "universelle")\n- Nécessite régularité de mesure (même heure, même conditions)\n\n## Sources\n\n- Plews et al. (2013). "Training Adaptation and Heart Rate Variability in Elite Endurance Athletes"\n- Buchheit, M. (2014). "Monitoring training status with HR measures"',
  ARRAY['hrv', 'recovery', 'training_adaptation', 'fatigue_management'],
  ARRAY['intermediate', 'advanced', 'elite'],
  'fr'
);

-- Document 3: Structure d'une séance VMA
INSERT INTO public.knowledge_docs (
  title,
  source,
  doc_type,
  content,
  topics,
  target_audience,
  language
) VALUES (
  'Structurer une Séance Intervalles VMA Efficace',
  'Daniels Running Formula (2013)',
  'book',
  E'# Entraînement par Intervalles à VMA\n\n## Définition\n\nLa **VMA (Vitesse Maximale Aérobie)** est la vitesse de course à laquelle un athlète atteint sa consommation maximale doxygène (VO2max).\n\n## Formats dIntervalles Classiques\n\n### Format Court (Développement VO2max)\n- **Distance**: 400-800m\n- **Intensité**: 95-100% VMA\n- **Récupération**: 50-75% du temps deffort (ex: 2min effort → 1min30 récup)\n- **Volume total**: 5-8% du volume hebdomadaire\n- **Exemple**: 10x400m @ VMA avec 90s récup jogging\n\n### Format Long (Seuil VO2max)\n- **Distance**: 1000-1600m\n- **Intensité**: 90-95% VMA\n- **Récupération**: Égale au temps deffort\n- **Volume total**: 6-10km\n- **Exemple**: 5x1000m @ 95% VMA avec 3min récup\n\n## Progression sur 4 Semaines\n\n**Semaine 1**: 8x400m (volume total 3.2km)\n**Semaine 2**: 10x400m (4km)\n**Semaine 3**: 6x800m (4.8km)\n**Semaine 4**: 5x1000m (5km) + récupération\n\n## Structure dune Séance Type\n\n### Échauffement (15-20min)\n1. 10min jogging léger (Zone 1-2)\n2. 5min accélérations progressives\n3. 4-6 strides de 100m\n\n### Corps de Séance\n**Exemple**: 6x800m @ allure 5km\n- Intervalle: 3min15s (allure 4:05/km)\n- Récupération: 2min30s jogging très lent\n\n### Retour au Calme (10min)\n- 10min jogging facile Zone 1\n\n## Fréquence Recommandée\n\n- **Débutant**: 1 séance VMA / 10-14 jours\n- **Intermédiaire**: 1 séance VMA / semaine\n- **Avancé**: 1-2 séances VMA / semaine (espacées de 3 jours min)\n\n## Erreurs à Éviter\n\n1. **Courir trop vite**: Les intervalles ne sont PAS des sprints max\n2. **Récupération insuffisante**: Respecter les temps de récup\n3. **Volume excessif**: Max 10% du kilométrage hebdomadaire\n\n## Calcul de la VMA\n\n**Test terrain**: \n- Courir 6 minutes à intensité maximale soutenable\n- Distance parcourue / 100 = VMA (ex: 1500m → VMA = 15 km/h)\n\n**Alternative**: Utiliser la meilleure performance 5km ou 10km récente',
  ARRAY['vma', 'intervals', 'vo2max', 'workout_structure', '5k', '10k'],
  ARRAY['beginner', 'intermediate', 'advanced'],
  'fr'
);

-- ============================================
-- PART 5: UTILITY VIEWS (Optional)
-- ============================================

-- Vue: Récupération récente de l'utilisateur
CREATE OR REPLACE VIEW public.user_recovery_status AS
SELECT 
  dm.user_id,
  AVG(dm.hrv_ms) as avg_hrv_7d,
  AVG(dm.sleep_duration_hours) as avg_sleep_7d,
  AVG(dm.fatigue_score) as avg_fatigue_7d,
  COUNT(*) as days_logged
FROM public.daily_metrics dm
WHERE dm.date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY dm.user_id;

COMMENT ON VIEW public.user_recovery_status IS 'Moyennes de récupération sur les 7 derniers jours (pour prompting IA)';

-- ============================================
-- COMPLETION MESSAGE
-- ============================================

DO $$
BEGIN
  RAISE NOTICE '✅ Initialization complete!';
  RAISE NOTICE 'Tables created: 7';
  RAISE NOTICE 'RLS policies: Enabled';
  RAISE NOTICE 'Triggers: 3';
  RAISE NOTICE 'Knowledge docs: 3 inserted';
  RAISE NOTICE '';
  RAISE NOTICE '🎯 Next Steps:';
  RAISE NOTICE '1. Test user signup (creates profile automatically)';
  RAISE NOTICE '2. Configure iOS Shortcut with your Supabase URL + API key';
  RAISE NOTICE '3. Test daily_metrics insertion from Shortcut';
END $$;
