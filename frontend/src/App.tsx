import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Send, FileText, Globe } from 'lucide-react';
import DocumentUpload from './components/DocumentUpload';
import DocumentList from './components/DocumentList';
import ChatInterface from './components/ChatInterface';
import { API_BASE_URL } from './apiConfig';
import './styles/App.css';
import { t } from './i18n';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [error, setError] = useState('');
  const [health, setHealth] = useState(null);
  const [language, setLanguage] = useState(() => {
    const saved = localStorage.getItem('mal_di_lang');
    return saved === 'ar' ? 'ar' : 'en';
  });

  useEffect(() => {
    checkHealth();
    loadDocuments();
    const interval = setInterval(loadDocuments, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    localStorage.setItem('mal_di_lang', language);
  }, [language]);

  const checkHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      setHealth(response.data);
    } catch (err) {
      console.error('Health check failed:', err);
      setError(t(language, 'error.unreachable'));
    }
  };

  const loadDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents`);
      setDocuments(Array.isArray(response.data?.documents) ? response.data.documents : []);
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const handleUpload = async (file) => {
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setActiveTab('chat');
      setSelectedDoc(response.data.document_id);
      loadDocuments();
    } catch (err) {
      const code = err.response?.status;
      if (code === 413) {
        setError(t(language, 'error.tooLarge'));
      } else {
        setError(t(language, 'error.uploadFailed'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Delete this document?')) return;
    
    try {
      await axios.delete(`${API_BASE_URL}/documents/${docId}`);
      loadDocuments();
      if (selectedDoc === docId) setSelectedDoc(null);
    } catch (err) {
      setError(t(language, 'error.deleteFailed'));
    }
  };

  return (
    <div className={`app ${language === 'ar' ? 'rtl' : ''}`} dir={language === 'ar' ? 'rtl' : 'ltr'} lang={language}>
      <header className="app-header">
        <div className="header-content">
          <h1>MAL Document Intelligence System</h1>
        </div>
        <div className="header-actions">
          <div className="lang-switch" title={t(language, 'lang.title')}>
            <Globe size={18} />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value === 'ar' ? 'ar' : 'en')}
              aria-label={t(language, 'lang.title')}
            >
              <option value="en">English</option>
              <option value="ar">العربية</option>
            </select>
          </div>
          {health?.models_loaded && (
            <div className="health-indicator">
              <span className={(health.models_loaded.qa || health.models_loaded.chat) ? 'status-online' : 'status-offline'}>
                ●
              </span>
              {(health.models_loaded.qa || health.models_loaded.chat) ? t(language, 'status.ready') : t(language, 'status.starting')}
            </div>
          )}
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      <div className="app-container">
        <nav className="sidebar">
          <button
            className={`nav-button ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            <Upload size={20} />
            <span>{t(language, 'nav.upload')}</span>
          </button>
          <button
            className={`nav-button ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            <FileText size={20} />
            <span>{t(language, 'nav.documents')}</span>
            {documents.length > 0 && (
              <span className="badge">{documents.length}</span>
            )}
          </button>
          <button
            className={`nav-button ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <Send size={20} />
            <span>{t(language, 'nav.qa')}</span>
          </button>
        </nav>

        <main className="main-content">
          {activeTab === 'upload' && (
            <DocumentUpload 
              onUpload={handleUpload} 
              loading={loading}
              language={language}
            />
          )}

          {activeTab === 'documents' && (
            <DocumentList 
              documents={documents}
              onDelete={handleDelete}
              onSelect={(doc) => {
                setSelectedDoc(doc.document_id);
                setActiveTab('chat');
              }}
              language={language}
            />
          )}

          {activeTab === 'chat' && (
            <ChatInterface 
              selectedDoc={selectedDoc}
              documents={documents}
              onSelectDoc={setSelectedDoc}
              language={language}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
