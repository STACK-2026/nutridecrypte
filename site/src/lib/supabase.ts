// Supabase client for NutriDécrypte.
// Reads PUBLIC_SUPABASE_URL + PUBLIC_SUPABASE_ANON_KEY from import.meta.env.
// Site stays 100% static at build time; this helper is available for pages
// that need live data (Phase 1 catalog, analytics, newsletter submissions).

const SUPABASE_URL = import.meta.env.PUBLIC_SUPABASE_URL || "";
const SUPABASE_ANON_KEY = import.meta.env.PUBLIC_SUPABASE_ANON_KEY || "";

export interface SupabaseFetchOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  headers?: Record<string, string>;
  body?: string;
}

export function supabaseConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
}

export function getSupabaseUrl(): string {
  return SUPABASE_URL;
}

export function getSupabaseAnonKey(): string {
  return SUPABASE_ANON_KEY;
}

export async function supabaseFetch<T = unknown>(
  path: string,
  options: SupabaseFetchOptions = {}
): Promise<T | null> {
  if (!supabaseConfigured()) {
    console.warn("[supabase] PUBLIC_SUPABASE_URL or PUBLIC_SUPABASE_ANON_KEY not set");
    return null;
  }

  const url = `${SUPABASE_URL}${path.startsWith("/") ? path : "/" + path}`;
  try {
    const response = await fetch(url, {
      method: options.method || "GET",
      headers: {
        apikey: SUPABASE_ANON_KEY,
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      body: options.body,
    });
    if (!response.ok) {
      console.warn(`[supabase] ${path}: ${response.status}`);
      return null;
    }
    if (response.status === 204) return null;
    return (await response.json()) as T;
  } catch (e) {
    console.warn(`[supabase] ${path} fetch failed`, e);
    return null;
  }
}
