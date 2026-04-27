import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Loader, Copy, Check } from 'lucide-react';
import '../styles/ChatInterface.css';
import { API_BASE_URL } from '../apiConfig';

function ChatInterface({ selectedDoc, documents, onSelectDoc }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: userMessage,
      sender: 'user'
    }]);

    setLoading(true);

    const hasIndexedDocs = documents.length > 0;
    try {
      const response = await axios.post(`${API_BASE_URL}/ask`, {
        question: userMessage,
        document_id: selectedDoc || null,
        use_rag: hasIndexedDocs,
      });

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: response.data.answer,
        sender: 'assistant',
        sources: response.data.sources,
        used_rag: response.data.used_rag
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: 'We could not get an answer. Please try again in a moment.',
        sender: 'error'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasDocs = documents.length > 0;

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Q&amp;A</h2>
        <div className="doc-selector">
          <label>Answer using:</label>
          <select
            value={selectedDoc || 'all'}
            onChange={(e) => onSelectDoc(e.target.value === 'all' ? null : e.target.value)}
            disabled={!hasDocs}
            title={!hasDocs ? 'Upload a document first' : ''}
          >
            <option value="all">All documents</option>
            {documents.map((doc) => (
              <option key={doc.document_id} value={doc.document_id}>
                {doc.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!hasDocs && (
        <div className="chat-rag-hint">
          Upload a document and wait until it is ready, then ask your question here.
        </div>
      )}

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <h3>Questions</h3>
            {hasDocs ? (
              <p>Type your question below.</p>
            ) : (
              <p>Upload a document first, then return here.</p>
            )}
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`message message-${msg.sender}`}>
            <div className="message-content">
              <div className="message-text">{msg.text}</div>
              
              {msg.sender === 'assistant' && msg.sources && msg.sources.length > 0 && (
                <div className="message-sources">
                  <details>
                    <summary>
                      References ({msg.sources.length})
                    </summary>
                    <div className="sources-list">
                      {msg.sources.map((source, idx) => (
                        <div key={idx} className="source-item">
                          <span className="source-number">{idx + 1}</span>
                          <p>{source.content}</p>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}

              {msg.sender === 'assistant' && (
                <button
                  className="copy-btn"
                  onClick={() => copyToClipboard(msg.text)}
                  title="Copy to clipboard"
                >
                  {copied ? <Check size={16} /> : <Copy size={16} />}
                </button>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message message-loading">
            <div className="loading-indicator">
              <Loader className="spinner" size={20} />
              <span>Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          placeholder={
            hasDocs
              ? 'Ask about your documents…'
              : 'Ask anything (upload files later for document Q&A)…'
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          dir="auto"
        />
        <button type="submit" disabled={loading || !input.trim()}>
          <Send size={20} />
        </button>
      </form>
    </div>
  );
}

export default ChatInterface;
