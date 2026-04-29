import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy } from 'pdfjs-dist';
// Vite resolves worker as URL for pdfjs
// @ts-expect-error bundler URL import
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { Loader, MessageSquare, FileWarning } from 'lucide-react';
import { API_BASE_URL, documentFileUrl } from '../apiConfig';
import '../styles/DocumentPreview.css';
import { t, type Lang } from '../i18n';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

type LayoutBlock = {
  text: string;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  source?: string;
};

type LayoutPage = {
  page_index: number;
  blocks: LayoutBlock[];
  source?: string;
};

type Detail = {
  document_id: string;
  name: string;
  status: string;
  layout_pages: LayoutPage[];
  analysis?: {
    document_type?: string;
    classification_summary?: string;
    fields?: { label?: string; value?: string; confidence?: string }[];
    entities?: { type?: string; value?: string }[];
    error?: string;
  } | null;
  error?: string | null;
};

function blocksForPage(layoutPages: LayoutPage[], zeroBasedIndex: number): LayoutBlock[] {
  const p = layoutPages.find((x) => x.page_index === zeroBasedIndex);
  return p?.blocks || [];
}

function PdfPageRow({
  pdf,
  pageNum,
  blocks,
}: {
  pdf: PDFDocumentProxy;
  pageNum: number;
  blocks: LayoutBlock[];
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const taskHolder: { task: { cancel: () => void; promise: Promise<void> } | null } = {
      task: null,
    };
    let cancelled = false;

    const run = async () => {
      try {
        const page = await pdf.getPage(pageNum);
        const scale = 1.35;
        const viewport = page.getViewport({ scale });
        if (cancelled) return;

        setSize({ w: viewport.width, h: viewport.height });

        const ctx = canvas.getContext('2d');
        if (!ctx || cancelled) return;
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        taskHolder.task = page.render({ canvasContext: ctx, viewport });
        await taskHolder.task.promise;
      } catch (e: unknown) {
        const name = e instanceof Error ? e.name : '';
        if (
          !cancelled &&
          name !== 'RenderingCancelledException' &&
          name !== 'AbortException'
        ) {
          console.warn('PDF page render:', e);
        }
      }
    };

    void run();

    return () => {
      cancelled = true;
      try {
        taskHolder.task?.cancel();
      } catch {
        /* ignore */
      }
    };
  }, [pdf, pageNum]);

  return (
    <div className="doc-preview__page-sheet">
      <div
        className="doc-preview__sheet-inner"
        style={{ width: size.w || 400, height: size.h || 560, position: 'relative' }}
      >
        <canvas ref={canvasRef} className="doc-preview__canvas" />
        {blocks.map((b, idx) => (
          <div
            key={idx}
            className={`doc-preview__hl doc-preview__hl--${b.source === 'native' ? 'native' : 'ocr'}`}
            style={{
              left: `${b.x0 * 100}%`,
              top: `${b.y0 * 100}%`,
              width: `${Math.max(0.15, (b.x1 - b.x0) * 100)}%`,
              height: `${Math.max(0.08, (b.y1 - b.y0) * 100)}%`,
            }}
            title={b.text}
          />
        ))}
      </div>
    </div>
  );
}

function ImagePreview({ documentId, blocks }: { documentId: string; blocks: LayoutBlock[] }) {
  const [dims, setDims] = useState({ w: 0, h: 0 });

  return (
    <div className="doc-preview__page-sheet">
      <div className="doc-preview__img-wrap">
        <img
          src={documentFileUrl(documentId)}
          alt=""
          className="doc-preview__img"
          onLoad={(e) => {
            const el = e.currentTarget;
            setDims({ w: el.naturalWidth, h: el.naturalHeight });
          }}
        />
        <div className="doc-preview__img-overlay">
          {blocks.map((b, idx) => (
            <div
              key={idx}
              className={`doc-preview__hl doc-preview__hl--${b.source === 'native' ? 'native' : 'ocr'}`}
              style={{
                left: `${b.x0 * 100}%`,
                top: `${b.y0 * 100}%`,
                width: `${Math.max(0.15, (b.x1 - b.x0) * 100)}%`,
                height: `${Math.max(0.08, (b.y1 - b.y0) * 100)}%`,
              }}
              title={b.text}
            />
          ))}
        </div>
      </div>
      {dims.w > 0 && (
        <p className="doc-preview__meta">{dims.w}×{dims.h}px</p>
      )}
    </div>
  );
}

export default function DocumentPreview({
  documentId,
  language,
  onOpenChat,
  onRefreshList,
}: {
  documentId: string | null;
  language: Lang;
  onOpenChat: () => void;
  onRefreshList?: () => void;
}) {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [pdfDoc, setPdfDoc] = useState<PDFDocumentProxy | null>(null);
  const [pdfErr, setPdfErr] = useState<string | null>(null);
  const listRefreshDone = useRef(false);
  const onRefreshListRef = useRef(onRefreshList);
  onRefreshListRef.current = onRefreshList;

  const docName = detail?.name ?? '';
  const docStatus = detail?.status;
  const isPdfFile = docName.toLowerCase().endsWith('.pdf');

  useEffect(() => {
    listRefreshDone.current = false;
    if (!documentId) {
      setDetail(null);
      setPdfDoc(null);
      return;
    }

    let stopped = false;
    let intervalId: number | null = null;

    const fetchOnce = async () => {
      try {
        const { data } = await axios.get<Detail>(
          `${API_BASE_URL}/documents/${documentId}`
        );
        if (stopped) return;
        setDetail(data);
        const refresh = onRefreshListRef.current;
        if (data.status === 'ready' && refresh && !listRefreshDone.current) {
          listRefreshDone.current = true;
          refresh();
        }
        if (data.status === 'ready' || data.status === 'failed') {
          if (intervalId != null) {
            window.clearInterval(intervalId);
            intervalId = null;
          }
        }
      } catch {
        if (!stopped) setDetail(null);
      }
    };

    void fetchOnce();
    intervalId = window.setInterval(() => {
      void fetchOnce();
    }, 1400);

    return () => {
      stopped = true;
      if (intervalId != null) window.clearInterval(intervalId);
    };
  }, [documentId]);

  useEffect(() => {
    if (docStatus !== 'failed') return;
    setPdfDoc((prev) => {
      try {
        prev?.destroy();
      } catch {
        /* ignore */
      }
      return null;
    });
    setPdfErr(null);
  }, [docStatus, documentId]);

  useEffect(() => {
    if (!documentId || !docName || !isPdfFile) {
      setPdfDoc(null);
      setPdfErr(null);
      return;
    }

    let cancelled = false;
    let loaded: PDFDocumentProxy | null = null;
    setPdfErr(null);

    (async () => {
      try {
        const loadingTask = pdfjsLib.getDocument({
          url: documentFileUrl(documentId),
          withCredentials: false,
        });
        const pdf = await loadingTask.promise;
        if (cancelled) {
          try {
            pdf.destroy();
          } catch {
            /* ignore */
          }
          return;
        }
        loaded = pdf;
        setPdfDoc(pdf);
      } catch (e: unknown) {
        if (!cancelled) setPdfErr(String(e));
      }
    })();

    return () => {
      cancelled = true;
      try {
        loaded?.destroy();
      } catch {
        /* ignore */
      }
    };
  }, [documentId, docName, isPdfFile]);

  if (!documentId) {
    return (
      <div className="doc-preview doc-preview--empty">
        <p>{t(language, 'preview.pickDoc')}</p>
      </div>
    );
  }

  const layoutPages = detail?.layout_pages || [];
  const analysis = detail?.analysis;
  const processing = detail?.status === 'processing';
  const failed = detail?.status === 'failed';

  return (
    <div className="doc-preview">
      <div className="doc-preview__toolbar">
        <h2>{t(language, 'preview.title')}</h2>
        <button type="button" className="doc-preview__chat-btn" onClick={onOpenChat}>
          <MessageSquare size={18} />
          {t(language, 'preview.openChat')}
        </button>
      </div>

      {processing && (
        <div className="doc-preview__banner doc-preview__banner--info">
          <Loader className="spinner" size={20} />
          <span>{t(language, 'preview.processing')}</span>
        </div>
      )}

      {failed && (
        <div className="doc-preview__banner doc-preview__banner--err">
          <FileWarning size={20} />
          <span>{detail?.error || t(language, 'preview.failed')}</span>
        </div>
      )}

      <div className="doc-preview__grid">
        <aside className="doc-preview__aside">
          <h3>{t(language, 'preview.classification')}</h3>
          {analysis?.error && (
            <p className="doc-preview__warn">{analysis.error}</p>
          )}
          <dl className="doc-preview__dl">
            <dt>{t(language, 'preview.docType')}</dt>
            <dd>{analysis?.document_type || (processing ? '…' : '—')}</dd>
            <dt>{t(language, 'preview.summary')}</dt>
            <dd>{analysis?.classification_summary || (processing ? '…' : '—')}</dd>
          </dl>

          <h3>{t(language, 'preview.fields')}</h3>
          <div className="doc-preview__table-wrap">
            <table className="doc-preview__table">
              <thead>
                <tr>
                  <th>{t(language, 'preview.colLabel')}</th>
                  <th>{t(language, 'preview.colValue')}</th>
                </tr>
              </thead>
              <tbody>
                {(analysis?.fields || []).length === 0 && !processing && (
                  <tr>
                    <td colSpan={2} className="doc-preview__muted">
                      {t(language, 'preview.noFields')}
                    </td>
                  </tr>
                )}
                {(analysis?.fields || []).map((f, i) => (
                  <tr key={i}>
                    <td>{f.label || '—'}</td>
                    <td>{f.value || '—'}</td>
                  </tr>
                ))}
                {processing && (
                  <tr>
                    <td colSpan={2} className="doc-preview__muted">…</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <h3>{t(language, 'preview.entities')}</h3>
          <ul className="doc-preview__entities">
            {(analysis?.entities || []).length === 0 && !processing && (
              <li className="doc-preview__muted">{t(language, 'preview.noEntities')}</li>
            )}
            {(analysis?.entities || []).map((e, i) => (
              <li key={i}>
                <strong>{e.type}</strong>: {e.value}
              </li>
            ))}
          </ul>

          <p className="doc-preview__legend">
            <span className="doc-preview__swatch doc-preview__swatch--native" /> {t(language, 'preview.legendNative')}
            <span className="doc-preview__swatch doc-preview__swatch--ocr" /> {t(language, 'preview.legendOcr')}
          </p>
        </aside>

        <section className="doc-preview__viewer">
          <h3>{t(language, 'preview.viewerTitle')}</h3>
          {!detail && <Loader className="spinner" />}
          {detail && isPdfFile && pdfErr && (
            <p className="doc-preview__warn">{pdfErr}</p>
          )}
          {detail && isPdfFile && pdfDoc && (
            <div className="doc-preview__pages">
              {Array.from({ length: pdfDoc.numPages }, (_, i) => (
                <PdfPageRow
                  key={i + 1}
                  pdf={pdfDoc}
                  pageNum={i + 1}
                  blocks={
                    detail.status === 'ready'
                      ? blocksForPage(layoutPages, i)
                      : []
                  }
                />
              ))}
            </div>
          )}
          {detail && !isPdfFile && detail.status !== 'failed' && (
            <ImagePreview
              documentId={documentId!}
              blocks={
                detail.status === 'ready' ? blocksForPage(layoutPages, 0) : []
              }
            />
          )}
        </section>
      </div>
    </div>
  );
}
