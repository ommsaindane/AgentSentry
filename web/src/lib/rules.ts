import { API_BASE } from "./api";

export type Rule = {
  id: number;
  name: string;
  pattern: string;
  rule_type: "regex" | "nlp";
  severity: "info" | "warning" | "critical";
  decision: "allow" | "warn" | "block";
  enabled: boolean;
  description?: string | null;
};

export async function listRules(): Promise<Rule[]> {
  const res = await fetch(`${API_BASE}/rules`, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function createRule(input: Omit<Rule, "id" | "enabled"> & { enabled?: boolean }) {
  const res = await fetch(`${API_BASE}/rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateRule(id: number, input: Partial<Omit<Rule, "id">>) {
  const res = await fetch(`${API_BASE}/rules/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function toggleRule(id: number, enabled: boolean) {
  const res = await fetch(`${API_BASE}/rules/${id}/toggle`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteRule(id: number) {
  const res = await fetch(`${API_BASE}/rules/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function importYaml(text: string) {
  const res = await fetch(`${API_BASE}/rules/import`, {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: text,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function exportYaml(): Promise<string> {
  const res = await fetch(`${API_BASE}/rules/export`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.yaml as string;
}
