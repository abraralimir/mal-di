import React from 'react';
import { Trash2, FileText, Calendar } from 'lucide-react';
import '../styles/DocumentList.css';

function DocumentList({ documents, onDelete, onSelect }) {
  if (documents.length === 0) {
    return (
      <div className="document-list-empty">
        <FileText size={48} />
        <h2>No documents yet</h2>
        <p>Upload a document to get started</p>
      </div>
    );
  }

  return (
    <div className="document-list-container">
      <h2>Your documents ({documents.length})</h2>
      <div className="documents-grid">
        {documents.map((doc) => (
          <div key={doc.document_id} className="document-card">
            <div className="card-header">
              <FileText size={24} />
              <h3 title={doc.name}>{doc.name}</h3>
            </div>
            <div className="card-body">
              <div className="info-item">
                <span>Status:</span>
                <strong>
                  {doc.status === 'ready'
                    ? 'Ready'
                    : doc.status === 'processing'
                      ? 'Processing'
                      : doc.status === 'failed'
                        ? 'Needs attention'
                        : doc.status}
                </strong>
              </div>
              <div className="info-item">
                <span>Text size:</span>
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
                Chat with this
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
