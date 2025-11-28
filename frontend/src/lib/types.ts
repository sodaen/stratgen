export type CitationSpan = { start: number; end: number } | null;
export interface CitationRef { doc_id: string; chunk_idx?: number; span?: CitationSpan; url?: string; title?: string; }
export interface PreviewDiagnostics { citations_count?: number; retrieval_k?: number; rerank_enabled?: boolean; dedup_count?: number; [k: string]: any; }
export interface OutlineSection { id?: string; title: string; bullets?: string[]; children?: OutlineSection[]; }
export interface PreviewResponse { outline?: { title?: string; sections?: OutlineSection[] }; bullets?: string[]; citations?: CitationRef[]; diagnostics?: PreviewDiagnostics; }
