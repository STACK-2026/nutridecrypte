// VPS Postgres client (STACK-2026 Tier-2). BUILD-TIME ONLY.
// Reads DATABASE_URL from the build env (process.env), reached via a Cloudflare
// Tunnel sidecar (cloudflared access tcp -> 127.0.0.1:5432). No SSL on the local
// tunnel hop; the tunnel encrypts edge-to-edge.
import postgres from "postgres";

const DATABASE_URL = process.env.DATABASE_URL || "";
let _sql: ReturnType<typeof postgres> | null = null;

export function dbConfigured(): boolean {
  return Boolean(DATABASE_URL);
}

export function db() {
  if (!_sql) {
    if (!DATABASE_URL) throw new Error("[db] DATABASE_URL not set at build time (VPS Postgres)");
    _sql = postgres(DATABASE_URL, { ssl: false, max: 4, idle_timeout: 20, connect_timeout: 30 });
  }
  return _sql;
}
