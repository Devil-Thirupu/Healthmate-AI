/**
 * supabaseClient.js
 *
 * Initialises the Supabase JS client for the HealthMate AI frontend.
 *
 * Only the VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY (anon/public)
 * keys are used here.  The service_role key is NEVER exposed to the frontend.
 *
 * The Supabase client is used for:
 *   - Auth session persistence (Supabase manages refresh token automatically)
 *   - onAuthStateChange listener (keeps AuthContext in sync)
 *   - Future: Google OAuth popup flow via Supabase Auth
 *
 * All medical data access goes through the FastAPI backend, NOT directly from
 * the frontend to Supabase tables.
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl || !supabasePublishableKey) {
  console.warn(
    '[HealthMate] Supabase environment variables are not set. ' +
    'Auth state persistence via Supabase will be disabled. ' +
    'Set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in frontend/.env'
  );
}

// createClient gracefully returns a client even if the vars are undefined;
// operations will fail with auth errors instead of crashing the app.
export const supabase = (supabaseUrl && supabasePublishableKey)
  ? createClient(supabaseUrl, supabasePublishableKey, {
      auth: {
        // Let Supabase manage session persistence in localStorage
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        // Use a HealthMate-prefixed key to avoid collisions
        storageKey: 'healthmate_supabase_session',
      },
    })
  : null;

export default supabase;
