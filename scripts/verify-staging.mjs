#!/usr/bin/env node
// Staging environment verification. Reads .env.staging.local (never committed).
//   node scripts/verify-staging.mjs            — read-only checks
//   node scripts/verify-staging.mjs --probe    — additionally creates + drops
//                                                public._startup_probe to prove
//                                                the anon key against real tables
// Prints results, exits non-zero on hard failures. Never prints secret values.
import { readFileSync } from "node:fs";
import { join } from "node:path";

const root = import.meta.dirname ? join(import.meta.dirname, "..") : process.cwd();
const lines = readFileSync(join(root, ".env.staging.local"), "utf8").split(/\r?\n/);
const vars = {};
for (const l of lines) {
  const m = l.match(/^([A-Z0-9_]+)=(.*)$/);
  if (m) vars[m[1]] = m[2];
}

const probe = process.argv.includes("--probe");
let hardFail = 0;

function mask(value) {
  return value ? `${value.slice(0, 4)}****${value.slice(-4)}` : "<missing>";
}

// --- Supabase ---------------------------------------------------------------
const ref = vars.SUPABASE_PROJECT_REF;
if (!ref || ref.length < 16) {
  console.log("FAIL  supabase ref missing/short");
  process.exit(1);
}
const sbBase = `https://${ref}.supabase.co`;
const mgmt = { Authorization: `Bearer ${vars.SUPABASE_ACCESS_TOKEN ?? ""}` };

// project status + region (management API)
try {
  const res = await fetch(`https://api.supabase.com/v1/projects/${ref}`, { headers: mgmt });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const p = await res.json();
  console.log(
    `PASS  supabase project ${p.id.slice(0, 4)}****  status=${p.status}  region=${p.region}`,
  );
} catch (e) {
  console.log(`FAIL  supabase management api — ${e.message}`);
  hardFail += 1;
}

// REST with service_role (gateway + signature check)
try {
  const res = await fetch(`${sbBase}/rest/v1/`, {
    headers: {
      apikey: vars.SUPABASE_SERVICE_ROLE_KEY,
      Authorization: `Bearer ${vars.SUPABASE_SERVICE_ROLE_KEY}`,
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const body = await res.json();
  console.log(`PASS  supabase rest/service_role — ${body.info?.title ?? "openapi"}`);
} catch (e) {
  console.log(`FAIL  supabase rest/service_role — ${e.message}`);
  hardFail += 1;
}

// anon key against a REAL table (root OpenAPI is known-401 for stranger roles on
// empty schemas — see DEVELOPMENT.md). --probe handles empty projects.
if (probe) {
  try {
    const q = await fetch(`https://api.supabase.com/v1/projects/${ref}/database/query`, {
      method: "POST",
      headers: { ...mgmt, "content-type": "application/json" },
      body: JSON.stringify({ query: "create table if not exists public._startup_probe (id int)" }),
    });
    if (!q.ok) throw new Error(`query HTTP ${q.status}`);
  } catch (e) {
    console.log(`FAIL  probe table create — ${e.message}`);
    hardFail += 1;
  }
}
try {
  const base = probe ? `${sbBase}/rest/v1/_startup_probe` : null;
  if (!base) throw new Error("no table guessed; use --probe on empty projects");
  let status = 0;
  let okResponse = null;
  for (let attempt = 0; attempt < 3; attempt++) {
    const res = await fetch(`${base}?select=id`, {
      headers: {
        apikey: vars.NEXT_PUBLIC_SUPABASE_ANON_KEY,
        Authorization: `Bearer ${vars.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,
      },
    });
    status = res.status;
    okResponse = res;
    if (res.ok) break;
    // PostgREST caches the schema; fresh tables can 404 on the first hit
    await new Promise((r) => setTimeout(r, 1500));
  }
  console.log(
    okResponse.ok
      ? `PASS  supabase rest/anon — table probe reachable (anon ${mask(vars.NEXT_PUBLIC_SUPABASE_ANON_KEY)})`
      : `FAIL  supabase rest/anon — HTTP ${status}`,
  );
  if (!okResponse.ok) hardFail += 1;
} catch (e) {
  console.log(`WARN  supabase rest/anon — ${e.message}`);
}

if (probe) {
  try {
    await fetch(`https://api.supabase.com/v1/projects/${ref}/database/query`, {
      method: "POST",
      headers: { ...mgmt, "content-type": "application/json" },
      body: JSON.stringify({ query: "drop table if exists public._startup_probe" }),
    });
    console.log("PASS  probe table dropped");
  } catch (e) {
    console.log(`WARN  probe table drop — ${e.message}`);
  }
}

// --- Sentry ------------------------------------------------------------------
const sentryHeaders = { Authorization: `Bearer ${vars.SENTRY_AUTH_TOKEN ?? ""}` };
try {
  const me = await fetch("https://sentry.io/api/0/users/me/", { headers: sentryHeaders });
  if (me.status === 403) {
    // Decode the embedded scope payload of sntrys_ tokens — zero-scope tokens
    // 403 everywhere and this tells the owner exactly why.
    try {
      const payloadB64 = vars.SENTRY_AUTH_TOKEN.split("_")[1];
      const json = JSON.parse(
        Buffer.from(payloadB64.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString("utf8"),
      );
      console.log(
        `FAIL  sentry token — scopes embedded: ${json.scopes ? JSON.stringify(json.scopes) : "NONE (token minted without scopes — recreate with org:read, project:read, project:releases, event:write)"}`,
      );
    } catch {
      console.log(`FAIL  sentry token — HTTP 403 at /users/me/ (token unusable)`);
    }
    hardFail += 1;
  } else if (!me.ok) {
    console.log(`FAIL  sentry token — HTTP ${me.status} at /users/me/`);
    hardFail += 1;
  } else {
    console.log("PASS  sentry token — /users/me/ accepted");
    // org + project + DSN cross-check are only meaningful with a working token
    try {
      const org = await fetch(
        `https://sentry.io/api/0/organizations/${vars.SENTRY_ORG}/`,
        { headers: sentryHeaders },
      );
      console.log(
        org.ok
          ? `PASS  sentry org '${vars.SENTRY_ORG}'`
          : `FAIL  sentry org '${vars.SENTRY_ORG}' — HTTP ${org.status}`,
      );
      if (!org.ok) hardFail += 1;
    } catch (e) {
      console.log(`FAIL  sentry org — ${e.message}`);
      hardFail += 1;
    }
    try {
      const proj = await fetch(
        `https://sentry.io/api/0/projects/${vars.SENTRY_ORG}/${vars.SENTRY_PROJECT}/`,
        { headers: sentryHeaders },
      );
      console.log(
        proj.ok
          ? `PASS  sentry project '${vars.SENTRY_PROJECT}'`
          : `FAIL  sentry project '${vars.SENTRY_PROJECT}' — HTTP ${proj.status}`,
      );
      if (!proj.ok) hardFail += 1;
    } catch (e) {
      console.log(`FAIL  sentry project — ${e.message}`);
      hardFail += 1;
    }
    try {
      const ck = await fetch(
        `https://sentry.io/api/0/projects/${vars.SENTRY_ORG}/${vars.SENTRY_PROJECT}/client-keys/`,
        { headers: sentryHeaders },
      );
      if (!ck.ok) throw new Error(`HTTP ${ck.status}`);
      const keys = await ck.json();
      const dsnKey = (vars.SENTRY_DSN ?? "").split("@")[0];
      const listed = Array.isArray(keys);
      const matched =
        listed &&
        keys.some(
          (k) => (k.dsn?.secret ?? k.secret ?? "").startsWith(dsnKey.slice(0, 16)),
        );
      console.log(
        matched
          ? `PASS  sentry DSN belongs to project '${vars.SENTRY_PROJECT}'`
          : `FAIL  sentry DSN key ${dsnKey.slice(0, 8)}**** not among project client keys`,
      );
      if (!matched) hardFail += 1;
    } catch (e) {
      console.log(`FAIL  sentry DSN cross-check — ${e.message}`);
      hardFail += 1;
    }
  }
} catch (e) {
  console.log(`FAIL  sentry token — ${e.message}`);
  hardFail += 1;
}

// Sentry DSN shape (no network)
const dsnOk = /^https:\/\/[0-9a-f]+@.*sentry\.[a-z.]+\/\d+$/.test(vars.SENTRY_DSN ?? "");
console.log(dsnOk ? "PASS  sentry DSN shape" : "FAIL  sentry DSN shape");
if (!dsnOk) hardFail += 1;

process.exit(hardFail > 0 ? 1 : 0);
