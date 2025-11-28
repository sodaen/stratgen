import React from "react";

type QItem = {
  id: string;
  file: File;
  progress: number; // 0..100
  status: "queued" | "uploading" | "done" | "error";
  url?: string;
  error?: string;
};

const UPLOAD_URL =
  (import.meta.env.VITE_UPLOAD_URL as string | undefined)?.replace(/\/$/, "") || "/files/upload";

export default function UploadDrop({
  tags,
  org,
  project,
  onUploaded,
}: {
  tags?: string;
  org?: string;
  project?: string;
  onUploaded?: (items: QItem[]) => void;
}) {
  const [queue, setQueue] = React.useState<QItem[]>([]);
  const [highlight, setHighlight] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement | null>(null);

  function addFiles(fs: FileList | null) {
    if (!fs || !fs.length) return;
    const ns: QItem[] = Array.from(fs).map((f) => ({
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      file: f,
      progress: 0,
      status: "queued",
    }));
    setQueue((q) => [...ns, ...q]);
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setHighlight(false);
    addFiles(e.dataTransfer.files);
  }

  function uploadOne(item: QItem) {
    return new Promise<QItem>((resolve) => {
      const form = new FormData();
      form.append("file", item.file);
      if (tags) form.append("tags", tags);
      if (org) form.append("org", org);
      if (project) form.append("project", project);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", UPLOAD_URL);
      xhr.upload.onprogress = (ev) => {
        if (!ev.lengthComputable) return;
        const p = Math.round((ev.loaded / ev.total) * 100);
        setQueue((q) => q.map((it) => (it.id === item.id ? { ...it, progress: p, status: "uploading" } : it)));
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          let url: string | undefined;
          try {
            const j = JSON.parse(xhr.responseText || "{}");
            url = j.url || j.path || undefined;
          } catch {}
          setQueue((q) => q.map((it) => (it.id === item.id ? { ...it, progress: 100, status: "done", url } : it)));
          resolve({ ...item, progress: 100, status: "done", url });
        } else {
          const err = `${xhr.status} ${xhr.statusText}`;
          setQueue((q) => q.map((it) => (it.id === item.id ? { ...it, status: "error", error: err } : it)));
          resolve({ ...item, status: "error", error: err });
        }
      };
      xhr.onerror = () => {
        const err = "network error";
        setQueue((q) => q.map((it) => (it.id === item.id ? { ...it, status: "error", error: err } : it)));
        resolve({ ...item, status: "error", error: err });
      };
      xhr.send(form);
    });
  }

  async function uploadAll() {
    const results: QItem[] = [];
    for (const it of queue.filter((x) => x.status === "queued" || x.status === "error")) {
      // eslint-disable-next-line no-await-in-loop
      const r = await uploadOne(it);
      results.push(r);
    }
    onUploaded?.(results);
  }

  function removeItem(id: string) {
    setQueue((q) => q.filter((i) => i.id !== id));
  }

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Uploads (Bilder · Zahlen · Daten · Fakten · Wissen)</h3>
      <div
        className={`drop ${highlight ? "highlight" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setHighlight(true);
        }}
        onDragLeave={() => setHighlight(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        aria-label="Dateien hier ablegen oder klicken zum Auswählen"
        tabIndex={0}
      >
        Dateien hier ablegen oder klicken zum Auswählen
        <div className="help">Akzeptiert beliebige Dateitypen. Upload-Endpoint: <code>{UPLOAD_URL}</code></div>
      </div>

      <input
        ref={inputRef}
        type="file"
        multiple
        style={{ display: "none" }}
        onChange={(e) => addFiles(e.target.files)}
      />

      <div className="actions" style={{ marginTop: 10 }}>
        <button className="fileBtn" onClick={() => inputRef.current?.click()}>Dateien wählen</button>
        <button
          className="fileBtn"
          onClick={uploadAll}
          disabled={!queue.some((q) => q.status === "queued" || q.status === "error")}
        >
          Upload starten
        </button>
        <span className="help">Queue: {queue.length} Datei(en)</span>
      </div>

      <div className="queue">
        {queue.map((f) => (
          <div className="fileRow" key={f.id}>
            <div title={f.file.name}>{f.file.name}</div>
            <div className="progressTrack" aria-label={`Upload-Fortschritt ${f.progress}%`}>
              <div className="progressBar" style={{ width: `${f.progress}%` }} />
            </div>
            <div className="stat">
              {f.status === "queued" && "wartet"}
              {f.status === "uploading" && `${f.progress}%`}
              {f.status === "done" && "fertig"}
              {f.status === "error" && `Fehler${f.error ? `: ${f.error}` : ""}`}
            </div>
            <button className="fileBtn" onClick={() => removeItem(f.id)} aria-label="entfernen">✕</button>
          </div>
        ))}
      </div>
    </div>
  );
}
