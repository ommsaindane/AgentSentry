import { api, type SessionListItem } from "../lib/api";

export default async function Page() {
  let sessions: SessionListItem[] = [];
  let error: string | null = null;

  try {
    sessions = await api.listSessions();
  } catch (e: any) {
    error = e?.message || "Failed to load sessions";
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Sessions</h1>
      {error ? (
        <div className="text-red-600 text-sm">{error}</div>
      ) : (
        <div className="border border-gray-200 rounded">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-2">ID</th>
                <th className="text-left p-2">Title</th>
                <th className="text-left p-2">Created</th>
                <th className="text-left p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.id} className="border-t">
                  <td className="p-2 font-mono">{s.id}</td>
                  <td className="p-2">{s.title ?? "-"}</td>
                  <td className="p-2">{s.created_at ?? "-"}</td>
                  <td className="p-2">
                    <a className="text-blue-600 hover:underline" href={`/traces/${encodeURIComponent(s.id)}`}>
                      View traces (by id)
                    </a>
                    <span className="text-gray-400 mx-2">|</span>
                    <a
                      className="text-gray-600 hover:underline"
                      href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/sessions`}
                      target="_blank"
                    >
                      Raw JSON
                    </a>
                  </td>
                </tr>
              ))}
              {sessions.length === 0 && (
                <tr>
                  <td className="p-2 text-gray-500" colSpan={4}>
                    No sessions yet. Use examples/send_trace.py to create one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      <div className="text-xs text-gray-500">
        Tip: POST /sessions and POST /traces from the SDK or curl; refresh to see new sessions.
      </div>
    </div>
  );
}