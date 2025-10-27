export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || "http://localhost:8000";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    // Ensure Next won't cache API responses during dev
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  return (await res.json()) as T;
}

export type SessionListItem = { id: string; title?: string | null; created_at?: string };
export type TraceDetail = {
  id: string;
  session_id: string;
  role: string;
  content: any;
  decision: "allow" | "warn" | "block";
  reasons: Array<{ rule: string; severity: string; decision: string; description?: string }>;
  created_at: string;
};

export const api = {
  listSessions: () => http<SessionListItem[]>("/sessions"),
  getTrace: (id: string) => http<TraceDetail>(`/traces/${id}`),
};