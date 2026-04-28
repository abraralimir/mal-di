import React from 'react';
import { Trash2, FileText, Calendar } from 'lucide-react';
import '../styles/DocumentList.css';
import { t, type Lang } from '../i18n';

function DocumentList({ documents, onDelete, onSelect, language }: { documents: any[]; onDelete: (id: string) => void; onSelect: (doc: any) => void; language: Lang }) {
  if (documents.length === 0) {
    return (
      <div className="document-list-empty">
        <FileText size={48} />
        <h2>{t(language, 'docs.emptyTitle')}</h2>
        <p>{t(language, 'docs.emptySubtitle')}</p>
      </div>
    );
  }

  return (
    <div className="document-list-container">
      <h2>{t(language, 'docs.title')} ({documents.length})</h2>
      <div className="documents-grid">
        {documents.map((doc) => (
          <div key={doc.document_id} className="document-card">
            <div className="card-header">
              <FileText size={24} />
              <h3 title={doc.name}>{doc.name}</h3>
            </div>
            <div className="card-body">
              <div className="info-item">
                <span>{t(language, 'docs.status')}:</span>
                <strong>
                  {doc.status === 'ready'
                    ? t(language, 'docs.ready')
                    : doc.status === 'processing'
                      ? t(language, 'docs.processing')
                      : doc.status === 'failed'
                        ? t(language, 'docs.needsAttention')
                        : doc.status}
                </strong>
              </div>
              <div className="info-item">
                <span>{t(language, 'docs.textSize')}:</span>
                <strong>{(doc.text_length / 1024).toFixed(1)} KB</strong>
              </div>
              <div className="info-item">
                <Calendar size={14} />
                <small>{new Date(doc.added_at).toLocaleDateString()}</small>
              </div>
            </div>
            <div className="card-actions">
              <button
                className="btn-select"
                onClick={() => onSelect(doc)}
              >
                {t(language, 'docs.chatWithThis')}
              </button>
              <button
                className="btn-delete"
                onClick={() => onDelete(doc.document_id)}
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default DocumentList;
