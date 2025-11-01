import { api } from "../../../lib/api";

export default async function SessionTracesPage({ params }: { params: { id: string } }) {
  const sessionId = params.id;
  let traces: Awaited<ReturnType<typeof api.listTracesForSession>> = [];
  let error: string | null = null;

  try {
    traces = await api.listTracesForSession(sessionId);
  } catch (e: any) {
    error = e?.message || "Failed to load traces";
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Session {sessionId}</h1>
      <div className="text-sm text-gray-500">Recent traces for this session.</div>
      {error ? (
        <div className="text-red-600 text-sm">{error}</div>
      ) : (
        <div className="border rounded overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-2">Trace ID</th>
                <th className="text-left p-2">Role</th>
                <th className="text-left p-2">Decision</th>
                <th className="text-left p-2">Created</th>
                <th className="text-left p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {traces.map((t) => (
                <tr key={t.id} className="border-t">
                  <td className="p-2 font-mono">{t.id}</td>
                  <td className="p-2">{t.role}</td>
                  <td className="p-2">
                    <span
                      className={
                        t.decision === "block"
                          ? "text-red-600"
                          : t.decision === "warn"
                          ? "text-yellow-600"
                          : "text-green-700"
                      }
                    >
                      {t.decision}
                    </span>
                  </td>
                  <td className="p-2">{t.created_at}</td>
                  <td className="p-2">
                    <a className="text-blue-600 hover:underline" href={`/traces/${encodeURIComponent(t.id)}`}>
                      View detail
                    </a>
                  </td>
                </tr>
              ))}
              {traces.length === 0 && (
                <tr>
                  <td className="p-2 text-gray-500" colSpan={5}>
                    No traces yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      <div className="text-xs text-gray-500">
        Raw JSON: <a className="text-blue-600" href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/sessions/${encodeURIComponent(sessionId)}/traces`} target="_blank" rel="noreferrer">/sessions/{sessionId}/traces</a>
      </div>
    </div>
  );
}
