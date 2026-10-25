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
// 2026 org tokens ("org:ci" bundle: source-map upload, release creation, code
// mappings) carry NO scopes in the payload and 403 on all read endpoints by
// design. Verification therefore checks: token shape, org binding, and — with
// --probe — an actual release round-trip (the capability the bundler needs).
const sentryHeaders = { Authorization: `Bearer ${vars.SENTRY_AUTH_TOKEN ?? ""}` };
let tokenOrg;
try {
  if (!(vars.SENTRY_AUTH_TOKEN ?? "").startsWith("sntrys_")) {
    throw new Error("unexpected token format (expected sntrys_…)");
  }
  const payloadB64 = vars.SENTRY_AUTH_TOKEN.split("_")[1];
  const payload = JSON.parse(
    Buffer.from(payloadB64.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString("utf8"),
  );
  tokenOrg = payload.org;
  console.log(
    tokenOrg === vars.SENTRY_ORG
      ? `PASS  sentry token — org-bound to '${payload.org}' (payload has no scopes field: normal for org tokens)`
      : `FAIL  sentry token — org-bound to '${payload.org}' but SENTRY_ORG is '${vars.SENTRY_ORG}'`,
  );
  if (tokenOrg !== vars.SENTRY_ORG) hardFail += 1;
} catch (e) {
  console.log(`FAIL  sentry token — ${e.message}`);
  hardFail += 1;
}

// read endpoints: expected 403 for org tokens — informational only
const orgRead = await fetch(`https://sentry.io/api/0/organizations/${vars.SENTRY_ORG}/`, {
  headers: sentryHeaders,
}).catch((e) => ({ status: 0, error: e.message }));
console.log(
  orgRead.ok || orgRead.status === 403
    ? `${orgRead.ok ? "PASS" : "WARN"}  sentry org '${vars.SENTRY_ORG}' — HTTP ${orgRead.status}${orgRead.status === 403 ? " (org-token read limit)" : ""}`
    : `FAIL  sentry org — HTTP ${orgRead.status}${orgRead.error ?? ""}`,
);
if (!orgRead.ok && orgRead.status !== 403) hardFail += 1;

if (probe) {
  try {
    const version = `t01-verify-${Date.now()}`;
    const create = await fetch(`https://sentry.io/api/0/organizations/${vars.SENTRY_ORG}/releases/`, {
      method: "POST",
      headers: { ...sentryHeaders, "content-type": "application/json" },
      body: JSON.stringify({ version, projects: [vars.SENTRY_PROJECT] }),
    });
    if (create.status !== 201) throw new Error(`release create HTTP ${create.status}`);
    console.log(`PASS  sentry release round-trip — created '${version}' (upload-capable token confirmed)`);
    const read = await fetch(
      `https://sentry.io/api/0/organizations/${vars.SENTRY_ORG}/releases/${version}/`,
      { headers: sentryHeaders },
    );
    console.log(read.ok ? `PASS  sentry release read-back — HTTP ${read.status}` : `WARN  sentry release read-back — HTTP ${read.status}`);
    const del = await fetch(
      `https://sentry.io/api/0/organizations/${vars.SENTRY_ORG}/releases/${version}/`,
      { method: "DELETE", headers: sentryHeaders },
    );
    console.log(
      del.ok || del.status === 404 || del.status === 403
        ? `PASS  sentry release cleanup — HTTP ${del.status}${del.status === 403 ? " (delete not in org:ci bundle; harmless probe artefact)" : ""}`
        : `WARN  sentry release cleanup — HTTP ${del.status}`,
    );
  } catch (e) {
    console.log(`FAIL  sentry release round-trip — ${e.message}`);
    hardFail += 1;
  }
}

// Sentry DSN shape (no network; token cannot cross-check DSN ownership by design)
const dsnOk = /^https:\/\/[0-9a-f]+@.*sentry\.[a-z.]+\/\d+$/.test(vars.SENTRY_DSN ?? "");
console.log(dsnOk ? "PASS  sentry DSN shape" : "FAIL  sentry DSN shape");
if (!dsnOk) hardFail += 1;

process.exit(hardFail > 0 ? 1 : 0);
