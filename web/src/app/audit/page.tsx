import { api } from "../../lib/api";

export default async function AuditPage({ searchParams }: { searchParams?: Record<string, string> }) {
  const q = Object.fromEntries(Object.entries(searchParams || {}).filter(([_, v]) => !!v));
  let logs: Awaited<ReturnType<typeof api.listAuditLogs>> = [];
  let error: string | null = null;
  try {
    logs = await api.listAuditLogs({ action: q["action"], target_type: q["target_type"] });
  } catch (e: any) {
    error = e?.message || "Failed to load audit logs";
  }
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Audit Logs</h1>
      <div className="text-sm text-gray-500">Recent actions (rules changes, blocks, etc.).</div>
      {error ? (
        <div className="text-red-600 text-sm">{error}</div>
      ) : (
        <div className="border rounded overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-2">Time</th>
                <th className="text-left p-2">Actor</th>
                <th className="text-left p-2">Action</th>
                <th className="text-left p-2">Target</th>
                <th className="text-left p-2">Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className="border-t align-top">
                  <td className="p-2 whitespace-nowrap">{l.created_at}</td>
                  <td className="p-2">{l.actor}</td>
                  <td className="p-2">{l.action}</td>
                  <td className="p-2">
                    <div className="text-xs text-gray-600">{l.target_type}</div>
                    <div className="text-xs font-mono">{l.target_id}</div>
                  </td>
                  <td className="p-2">
                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">{JSON.stringify(l.details, null, 2)}</pre>
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td className="p-2 text-gray-500" colSpan={5}>
                    No audit logs yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      <div className="text-xs text-gray-500">
        Raw JSON: <a className="text-blue-600" href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/audit/logs`} target="_blank" rel="noreferrer">/audit/logs</a>
      </div>
    </div>
  );
}
