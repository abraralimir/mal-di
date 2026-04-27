import React from 'react';
import { Upload, Loader } from 'lucide-react';
import '../styles/DocumentUpload.css';

function DocumentUpload({ onUpload, loading }) {
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
          <h2>Upload a document</h2>
          <p>PDF or image. Arabic and English supported.</p>

          <label className="upload-input">
            {loading ? (
              <div className="loading-state">
                <Loader className="spinner" size={24} />
                <span>Uploading…</span>
              </div>
            ) : (
              <>
                <span className="upload-button">Choose file</span>
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
