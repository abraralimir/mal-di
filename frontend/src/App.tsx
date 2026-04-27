import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Send, FileText, Link2 } from 'lucide-react';
import DocumentUpload from './components/DocumentUpload';
import DocumentList from './components/DocumentList';
import ChatInterface from './components/ChatInterface';
import ConnectionsSettings from './components/ConnectionsSettings';
import { API_BASE_URL } from './apiConfig';
import './styles/App.css';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [error, setError] = useState('');
  const [health, setHealth] = useState(null);

  useEffect(() => {
    checkHealth();
    loadDocuments();
    const interval = setInterval(loadDocuments, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      setHealth(response.data);
    } catch (err) {
      console.error('Health check failed:', err);
      setError('Unable to reach the service. If it was just started, wait a few seconds and refresh.');
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
        setError('That file is too large. Try a smaller document.');
      } else {
        setError('We could not upload that file. Please try again.');
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
      setError('Failed to delete document');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>MAL Document Intelligence System</h1>
        </div>
        {health?.models_loaded && (
          <div className="health-indicator">
            <span className={(health.models_loaded.qa || health.models_loaded.chat) ? 'status-online' : 'status-offline'}>
              ●
            </span>
            {(health.models_loaded.qa || health.models_loaded.chat) ? 'Ready' : 'Starting…'}
          </div>
        )}
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
            <span>Upload</span>
          </button>
          <button
            className={`nav-button ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            <FileText size={20} />
            <span>Documents</span>
            {documents.length > 0 && (
              <span className="badge">{documents.length}</span>
            )}
          </button>
          <button
            className={`nav-button ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <Send size={20} />
            <span>Q&A</span>
          </button>
          <button
            className={`nav-button ${activeTab === 'connections' ? 'active' : ''}`}
            onClick={() => setActiveTab('connections')}
          >
            <Link2 size={20} />
            <span>Connections</span>
          </button>
        </nav>

        <main className="main-content">
          {activeTab === 'upload' && (
            <DocumentUpload 
              onUpload={handleUpload} 
              loading={loading}
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
            />
          )}

          {activeTab === 'chat' && (
            <ChatInterface 
              selectedDoc={selectedDoc}
              documents={documents}
              onSelectDoc={setSelectedDoc}
            />
          )}

          {activeTab === 'connections' && (
            <ConnectionsSettings
              onSaved={() => {
                checkHealth();
                loadDocuments();
              }}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
