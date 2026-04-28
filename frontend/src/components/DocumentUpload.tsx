import React from 'react';
import { Upload, Loader } from 'lucide-react';
import '../styles/DocumentUpload.css';
import { t, type Lang } from '../i18n';

function DocumentUpload({ onUpload, loading, language }: { onUpload: (f: File) => void; loading: boolean; language: Lang }) {
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-section upload-section--minimal">
        <div className="upload-box">
          <Upload size={48} />
          <h2>{t(language, 'upload.title')}</h2>
          <p>{t(language, 'upload.subtitle')}</p>

          <label className="upload-input">
            {loading ? (
              <div className="loading-state">
                <Loader className="spinner" size={24} />
                <span>{t(language, 'upload.uploading')}</span>
              </div>
            ) : (
              <>
                <span className="upload-button">{t(language, 'upload.choose')}</span>
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.webp"
                  disabled={loading}
                />
              </>
            )}
          </label>
        </div>
      </div>
    </div>
  );
}

export default DocumentUpload;
