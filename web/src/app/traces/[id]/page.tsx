export const dynamic = "force-dynamic";
import { api } from "../../../lib/api";

export default async function TraceDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let data: Awaited<ReturnType<typeof api.getTrace>> | null = null;
  let error: string | null = null;

  try {
    data = await api.getTrace(id);
  } catch (e: any) {
    error = e?.message || "Failed to load trace";
  }

  if (error) {
    return (
      <div>
        <h1 className="text-xl font-semibold mb-2">Trace {id}</h1>
        <div className="text-red-600 text-sm">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Trace {data.id}</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border rounded p-3">
          <div className="text-sm text-gray-500 mb-2">Summary</div>
          <div className="text-sm">
            <div><span className="text-gray-500">Session:</span> <span className="font-mono">{data.session_id}</span></div>
            <div><span className="text-gray-500">Role:</span> {data.role}</div>
            <div><span className="text-gray-500">Decision:</span> <span className={
              data.decision === "block" ? "text-red-600" : data.decision === "warn" ? "text-yellow-600" : "text-green-700"
            }>{data.decision}</span></div>
            <div><span className="text-gray-500">Created:</span> {data.created_at}</div>
          </div>
        </div>
        <div className="border rounded p-3">
          <div className="text-sm text-gray-500 mb-2">Reasons</div>
          {data.reasons?.length ? (
            <ul className="list-disc ml-5 text-sm">
              {data.reasons.map((r, i) => (
                <li key={i}>
                  <span className="font-mono">{r.rule}</span> — {r.severity} → {r.decision}
                  {r.description ? <span className="text-gray-500"> — {r.description}</span> : null}
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-sm text-gray-500">None</div>
          )}
        </div>
      </div>
      <div className="border rounded p-3">
        <div className="text-sm text-gray-500 mb-2">Payload</div>
        <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">{JSON.stringify(data.content, null, 2)}</pre>
      </div>
      <div className="text-xs text-gray-500">
        Raw JSON: <a className="text-blue-600" href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/traces/${data.id}`} target="_blank" rel="noreferrer">/traces/{data.id}</a>
      </div>
    </div>
  );
}