"use client";

import { useEffect, useState } from "react";
import {
  listRules,
  createRule,
  updateRule,
  toggleRule,
  deleteRule,
  importYaml,
  exportYaml,
  type Rule,
} from "../../lib/rules";
import { API_BASE } from "../../lib/api";

// Literal unions for select inputs
const severities = ["info", "warning", "critical"] as const;
type Severity = (typeof severities)[number];

const decisions = ["allow", "warn", "block"] as const;
type Decision = (typeof decisions)[number];

const ruleTypes = ["regex", "nlp"] as const;
type RuleType = (typeof ruleTypes)[number];

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [form, setForm] = useState<{
    name: string;
    pattern: string;
    rule_type: RuleType;
    severity: Severity;
    decision: Decision;
    enabled: boolean;
    description: string;
  }>({
    name: "",
    pattern: "",
    rule_type: "regex",
    severity: "warning",
    decision: "warn",
    enabled: true,
    description: "",
  });

  async function refresh() {
    setLoading(true);
    setErr(null);
    try {
      setRules(await listRules());
    } catch (e: any) {
      setErr(e?.message ?? "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createRule(form);
      setForm({
        name: "",
        pattern: "",
        rule_type: "regex",
        severity: "warning",
        decision: "warn",
        enabled: true,
        description: "",
      });
      await refresh();
    } catch (e: any) {
      alert(e?.message ?? "Create failed");
    }
  }

  async function onToggle(id: number, enabled: boolean) {
    try {
      await toggleRule(id, enabled);
      await refresh();
    } catch (e: any) {
      alert(e?.message ?? "Toggle failed");
    }
  }

  async function onDelete(id: number) {
    if (!confirm("Delete rule?")) return;
    try {
      await deleteRule(id);
      await refresh();
    } catch (e: any) {
      alert(e?.message ?? "Delete failed");
    }
  }

  async function onExport() {
    try {
      const yaml = await exportYaml();
      const blob = new Blob([yaml], { type: "text/yaml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "rules.yaml";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(e?.message ?? "Export failed");
    }
  }

  async function onImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    try {
      await importYaml(text);
      await refresh();
    } catch (e: any) {
      alert(e?.message ?? "Import failed");
    } finally {
      e.target.value = "";
    }
  }

  // Prompt helpers with explicit narrowing
  function promptSeverity(current: Severity): Severity {
    const v = (prompt("Severity (info|warning|critical)", current) ?? current) as string;
    return severities.includes(v as Severity) ? (v as Severity) : current;
  }
  function promptDecision(current: Decision): Decision {
    const v = (prompt("Decision (allow|warn|block)", current) ?? current) as string;
    return decisions.includes(v as Decision) ? (v as Decision) : current;
  }
  function promptRuleType(current: RuleType): RuleType {
    const v = (prompt("Type (regex|nlp)", current) ?? current) as string;
    return ruleTypes.includes(v as RuleType) ? (v as RuleType) : current;
  }

  async function onEdit(r: Rule) {
    const name = ((prompt("Name", r.name) ?? r.name) as string).trim();
    const pattern = ((prompt("Pattern", r.pattern) ?? r.pattern) as string).trim();
    const severity = promptSeverity(r.severity);
    const decision = promptDecision(r.decision);
    const rule_type = promptRuleType(r.rule_type);
    const description = ((prompt("Description", r.description ?? "") ?? (r.description ?? "")) as string).trim();

    try {
      await updateRule(r.id, { name, pattern, rule_type, severity, decision, description });
      await refresh();
    } catch (e: any) {
      alert(e?.message ?? "Update failed");
    }
  }

  async function onReload() {
    try {
      await fetch(`${API_BASE}/rules/reload`, { method: "POST" });
      await refresh();
      alert("Reloaded rules into verifier");
    } catch (e: any) {
      alert(e?.message ?? "Reload failed");
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Rules</h1>

      <div className="flex items-center gap-3">
        <button onClick={onExport} className="px-3 py-1 border rounded bg-gray-50">
          Export YAML
        </button>
        <label className="px-3 py-1 border rounded bg-gray-50 cursor-pointer">
          Import YAML
          <input type="file" accept=".yaml,.yml" className="hidden" onChange={onImport} />
        </label>
        <button onClick={refresh} className="px-3 py-1 border rounded">
          Refresh
        </button>
        <button onClick={onReload} className="px-3 py-1 border rounded bg-green-600 text-white">
          Reload Verifier
        </button>
      </div>

      <form onSubmit={onCreate} className="border rounded p-3 grid grid-cols-1 md:grid-cols-3 gap-2">
        <input
          className="border rounded p-2"
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <input
          className="border rounded p-2 md:col-span-2"
          placeholder={form.rule_type === "regex" ? "Pattern (regex)" : "Pattern (plain phrase or phrases | separated)"}
          value={form.pattern}
          onChange={(e) => setForm({ ...form, pattern: e.target.value })}
          required
        />
        <select
          className="border rounded p-2"
          value={form.rule_type}
          onChange={(e) => setForm({ ...form, rule_type: e.target.value as RuleType })}
        >
          {ruleTypes.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          className="border rounded p-2"
          value={form.severity}
          onChange={(e) => setForm({ ...form, severity: e.target.value as Severity })}
        >
          {severities.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          className="border rounded p-2"
          value={form.decision}
          onChange={(e) => setForm({ ...form, decision: e.target.value as Decision })}
        >
          {decisions.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <input
          className="border rounded p-2 md:col-span-2"
          placeholder="Description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.enabled}
            onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
          />
          Enabled
        </label>
        <div className="md:col-span-3">
          <button type="submit" className="px-3 py-1 border rounded bg-blue-600 text-white">
            Create
          </button>
        </div>
      </form>

      {loading ? (
        <div className="text-sm text-gray-500">Loading...</div>
      ) : err ? (
        <div className="text-sm text-red-600">{err}</div>
      ) : (
        <div className="border rounded overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-2">ID</th>
                <th className="text-left p-2">Name</th>
                <th className="text-left p-2">Type</th>
                <th className="text-left p-2">Pattern</th>
                <th className="text-left p-2">Severity</th>
                <th className="text-left p-2">Decision</th>
                <th className="text-left p-2">Enabled</th>
                <th className="text-left p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.id} className="border-t align-top">
                  <td className="p-2">{r.id}</td>
                  <td className="p-2">{r.name}</td>
                  <td className="p-2">{r.rule_type}</td>
                  <td className="p-2">
                    <code className="text-xs">{r.pattern}</code>
                  </td>
                  <td className="p-2">{r.severity}</td>
                  <td className="p-2">{r.decision}</td>
                  <td className="p-2">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={r.enabled}
                        onChange={(e) => onToggle(r.id, e.target.checked)}
                      />
                      <span className="text-xs">{r.enabled ? "on" : "off"}</span>
                    </label>
                  </td>
                  <td className="p-2">
                    <button className="text-blue-600 mr-3" onClick={() => onEdit(r)}>
                      Edit
                    </button>
                    <button className="text-red-600" onClick={() => onDelete(r.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {rules.length === 0 && (
                <tr>
                  <td className="p-2 text-gray-500" colSpan={8}>
                    No rules yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
