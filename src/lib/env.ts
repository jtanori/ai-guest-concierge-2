/**
 * Small, explicit env accessor. No magic — keys are read from process.env.
 * The required-key list is asserted by tests/env.example.test.ts and
 * surfaced at startup in T03+.
 */
export const REQUIRED_ENV_KEYS = [
  "NEXT_PUBLIC_SUPABASE_URL",
  "NEXT_PUBLIC_SUPABASE_ANON_KEY",
] as const;

export function missingEnvKeys(
  env: Record<string, string | undefined> = process.env,
  required: readonly string[] = REQUIRED_ENV_KEYS,
): string[] {
  return required.filter((key) => {
    const value = env[key];
    return value === undefined || value.trim() === "";
  });
}
