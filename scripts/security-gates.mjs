#!/usr/bin/env node
// Security gates enforced in CI (pnpm run check:security).
// Every rule here must have a proven negative control — see the
// security-gates-negative-control job in .github/workflows/ci.yml.
// Rules:
//   1. The Supabase service-role key may only be referenced inside
//      src/lib/server/ (webhook/queue workers). Never in the client bundle.
//   2. LLM provider SDKs may only be imported inside src/lib/provider.ts
//      (active as soon as that file exists — Phase 1, T55).
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

const srcRoot = process.argv[2] ?? "src";
const violations = [];

function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name === ".next") continue;
      walk(p);
    } else if (/\.(ts|tsx|js|jsx|mjs|cjs)$/.test(entry.name)) {
      scan(p);
    }
  }
}

function scan(file) {
  const rel = relative(srcRoot, file).split(sep).join("/");
  const text = readFileSync(file, "utf8");

  // Rule 1 — service-role key is server-only.
  if (/SUPABASE_SERVICE_ROLE_KEY/.test(text) && !rel.startsWith("lib/server/")) {
    violations.push(
      `${rel}: SUPABASE_SERVICE_ROLE_KEY referenced outside src/lib/server/ (server-only, workers only)`,
    );
  }

  // Rule 2 — all model access goes through the thin provider proxy.
  const providerFile = join(srcRoot, "lib", "provider.ts");
  if (existsSync(providerFile) && !rel.startsWith("lib/provider")) {
    if (/(from|import|require)\s*\(?\s*["'](openai|@anthropic-ai\/sdk)["']/.test(text)) {
      violations.push(`${rel}: LLM SDK imported outside src/lib/provider.ts (ADR-0001)`);
    }
  }
}

if (!statSync(srcRoot).isDirectory()) {
  console.error(`security gates: source root not found: ${srcRoot}`);
  process.exit(2);
}

walk(srcRoot);

if (violations.length > 0) {
  console.error("Security gate violations:");
  for (const v of violations) console.error(`  - ${v}`);
  process.exit(1);
}
console.log("security gates: clean");
