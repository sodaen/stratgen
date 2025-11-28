export type StreamHandler<T=any> = (evt: T) => void;

export async function postJSONStream<T=any>(
  url: string,
  init: RequestInit & { signal?: AbortSignal } = {},
  onEvent?: StreamHandler<T>
): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const txt = await res.text().catch(()=> "");
    throw new Error(`HTTP ${res.status}: ${txt || res.statusText}`);
  }
  const ct = (res.headers.get("Content-Type") || "").toLowerCase();
  const isStream = !!res.body && (ct.includes("ndjson") || ct.includes("event-stream") || ct.includes("text/plain"));
  if (!isStream) {
    // Fallback: normale JSON-Antwort
    if (ct.includes("application/json")) {
      const j = await res.json();
      onEvent && onEvent(j);
      return j;
    } else {
      const t = await res.text();
      try { const j = JSON.parse(t); onEvent && onEvent(j); return j; } catch { return t as any; }
    }
  }
  // Streaming (NDJSON oder SSE-ähnliche "data:"-Zeilen)
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  let last: any = null;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, idx).trim();
      buf = buf.slice(idx + 1);
      if (!line) continue;
      let payload = line.startsWith("data:") ? line.replace(/^data:\s*/,"") : line;
      try { const obj = JSON.parse(payload); last = obj; onEvent && onEvent(obj); } catch {}
    }
  }
  const tail = decoder.decode();
  if (tail && tail.trim()) {
    try { const obj = JSON.parse(tail); last = obj; onEvent && onEvent(obj); } catch {}
  }
  return last as T;
}
