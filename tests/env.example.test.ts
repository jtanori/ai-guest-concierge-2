import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { REQUIRED_ENV_KEYS, missingEnvKeys } from "@/lib/env";

const repoRoot = resolve(import.meta.dirname, "..");
const example = readFileSync(resolve(repoRoot, ".env.example"), "utf8");

function valueFor(key: string): string | undefined {
  const line = example
    .split("\n")
    .find((l) => l.startsWith(`${key}=`));
  return line?.split("=").slice(1).join("=");
}

describe(".env.example template", () => {
  it("covers every required env key", () => {
    for (const key of REQUIRED_ENV_KEYS) {
      expect(valueFor(key), `missing ${key} in .env.example`).toBeDefined();
    }
  });

  it("uses placeholder or blank values only (no real-looking credentials)", () => {
    const nonSecretKeys = ["SENTRY_ENVIRONMENT", "NEXT_PUBLIC_APP_URL"];
    for (const line of example.split("\n")) {
      if (!line || line.startsWith("#") || !line.includes("=")) continue;
      const key = line.split("=", 1)[0];
      const value = line.slice(key.length + 1);
      const isAcceptable =
        value === "" ||
        value.startsWith("<") ||
        value.startsWith("http://127.0.0.1") ||
        value.startsWith("http://localhost") ||
        (nonSecretKeys.includes(key) && /^[a-z0-9._-]*$/.test(value));
      expect(isAcceptable, `suspicious real-looking value for ${key}`).toBe(true);
    }
  });

  it("never exposes the service-role key as a public var", () => {
    expect(example).not.toMatch(/^NEXT_PUBLIC[A-Z_]*SERVICE_ROLE/m);
  });

  it("declares all documented provider/infra keys", () => {
    const expected = [
      "NEXT_PUBLIC_SUPABASE_URL",
      "NEXT_PUBLIC_SUPABASE_ANON_KEY",
      "SUPABASE_SERVICE_ROLE_KEY",
      "SENTRY_DSN",
      "NEXT_PUBLIC_SENTRY_DSN",
      "SENTRY_AUTH_TOKEN",
      "ANTHROPIC_API_KEY",
      "OPENAI_API_KEY",
      "RESEND_API_KEY",
    ];
    for (const key of expected) {
      expect(example).toMatch(new RegExp(`^${key}=`, "m"));
    }
  });
});

describe("missingEnvKeys", () => {
  it("reports missing required keys", () => {
    const missing = missingEnvKeys({}, ["A", "B"]);
    expect(missing).toEqual(["A", "B"]);
  });

  it("treats blank strings as missing", () => {
    const missing = missingEnvKeys({ A: "  " }, ["A"]);
    expect(missing).toEqual(["A"]);
  });

  it("returns empty when all present", () => {
    expect(missingEnvKeys({ A: "x" }, ["A"])).toEqual([]);
  });
});
