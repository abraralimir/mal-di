import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Loader, Save } from 'lucide-react';
import { API_BASE_URL } from '../apiConfig';
import '../styles/ConnectionsSettings.css';

const KEEP = '__KEEP__';

type ConnectorForm = {
  base_url: string;
  pool_connections: number;
  pool_maxsize: number;
  http_timeout_sec: number;
  username: string;
  password: string;
  bearer_token: string;
};

const emptyConnector = (): ConnectorForm => ({
  base_url: '',
  pool_connections: 10,
  pool_maxsize: 32,
  http_timeout_sec: 120,
  username: '',
  password: KEEP,
  bearer_token: KEEP,
});

function ConnectionsSettings({ onSaved }: { onSaved?: () => void }) {
  const [bpm, setBpm] = useState<ConnectorForm>(emptyConnector);
  const [filenet, setFilenet] = useState<ConnectorForm>(emptyConnector);
  const [runtime, setRuntime] = useState<{ ibm_bpm: object | null; filenet: object | null } | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await axios.get(`${API_BASE_URL}/integrations/settings`);
      const f = data.form;
      setBpm({
        base_url: f.ibm_bpm.base_url ?? '',
        pool_connections: Number(f.ibm_bpm.pool_connections) || 10,
        pool_maxsize: Number(f.ibm_bpm.pool_maxsize) || 32,
        http_timeout_sec: Number(f.ibm_bpm.http_timeout_sec) || 120,
        username: f.ibm_bpm.username ?? '',
        password: KEEP,
        bearer_token: KEEP,
      });
      setFilenet({
        base_url: f.filenet.base_url ?? '',
        pool_connections: Number(f.filenet.pool_connections) || 10,
        pool_maxsize: Number(f.filenet.pool_maxsize) || 32,
        http_timeout_sec: Number(f.filenet.http_timeout_sec) || 120,
        username: f.filenet.username ?? '',
        password: KEEP,
        bearer_token: KEEP,
      });
      setRuntime(data.runtime);
    } catch (e) {
      setError('Could not load connection settings.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const save = async () => {
    setSaving(true);
    setMessage('');
    setError('');
    try {
      const { data } = await axios.put(`${API_BASE_URL}/integrations/settings`, {
        ibm_bpm: bpm,
        filenet: filenet,
      });
      setRuntime(data.runtime);
      setBpm((prev) => ({ ...prev, password: KEEP, bearer_token: KEEP }));
      setFilenet((prev) => ({ ...prev, password: KEEP, bearer_token: KEEP }));
      setMessage('Saved. Pools were recreated with these values.');
      onSaved?.();
    } catch (e: unknown) {
      setError('Save failed. Check values and try again.');
    } finally {
      setSaving(false);
    }
  };

  const renderBlock = (
    title: string,
    state: ConnectorForm,
    setState: React.Dispatch<React.SetStateAction<ConnectorForm>>,
    rtKey: 'ibm_bpm' | 'filenet'
  ) => (
    <section className="conn-block">
      <h3>{title}</h3>
      <p className="conn-hint">
        Base URL must include host and port. Document fetch URLs must match this host exactly.
      </p>
      <label>
        Base URL
        <input
          type="url"
          value={state.base_url}
          onChange={(e) => setState((s) => ({ ...s, base_url: e.target.value }))}
          placeholder="https://server:9443/your-root"
          autoComplete="off"
        />
      </label>
      <div className="conn-row">
        <label>
          Pool connections
          <input
            type="number"
            min={1}
            max={200}
            value={state.pool_connections}
            onChange={(e) =>
              setState((s) => ({ ...s, pool_connections: parseInt(e.target.value, 10) || 1 }))
            }
          />
        </label>
        <label>
          Pool max size
          <input
            type="number"
            min={1}
            max={200}
            value={state.pool_maxsize}
            onChange={(e) =>
              setState((s) => ({ ...s, pool_maxsize: parseInt(e.target.value, 10) || 1 }))
            }
          />
        </label>
        <label>
          Timeout (sec)
          <input
            type="number"
            min={5}
            max={900}
            step={1}
            value={state.http_timeout_sec}
            onChange={(e) =>
              setState((s) => ({ ...s, http_timeout_sec: parseFloat(e.target.value) || 120 }))
            }
          />
        </label>
      </div>
      <label>
        Username (optional)
        <input
          type="text"
          value={state.username}
          onChange={(e) => setState((s) => ({ ...s, username: e.target.value }))}
          autoComplete="off"
        />
      </label>
      <label>
        Password (optional)
        <input
          type="password"
          value={state.password === KEEP ? '' : state.password}
          placeholder={state.password === KEEP ? 'unchanged — type to replace' : ''}
          onChange={(e) =>
            setState((s) => ({
              ...s,
              password: e.target.value === '' ? KEEP : e.target.value,
            }))
          }
        />
      </label>
      <label>
        Bearer token (optional)
        <input
          type="password"
          value={state.bearer_token === KEEP ? '' : state.bearer_token}
          placeholder={state.bearer_token === KEEP ? 'unchanged — type to replace' : ''}
          onChange={(e) =>
            setState((s) => ({
              ...s,
              bearer_token: e.target.value === '' ? KEEP : e.target.value,
            }))
          }
        />
      </label>
      {runtime && runtime[rtKey] && (
        <div className="conn-runtime">
          <strong>Active pool</strong>
          <pre>{JSON.stringify(runtime[rtKey], null, 2)}</pre>
        </div>
      )}
      {runtime && !runtime[rtKey] && (
        <p className="conn-inactive">No pool (set a base URL and save).</p>
      )}
    </section>
  );

  if (loading) {
    return (
      <div className="conn-loading">
        <Loader className="spinner" size={28} />
        <span>Loading…</span>
      </div>
    );
  }

  return (
    <div className="conn-root">
      <header className="conn-header">
        <h2>Connections</h2>
        <p className="conn-lead">
          Configure HTTP connection pools for IBM BPM and FileNet (or any same-host REST root). Settings are stored on the server and applied immediately when you save.
        </p>
      </header>

      {error && <div className="conn-banner conn-error">{error}</div>}
      {message && <div className="conn-banner conn-success">{message}</div>}

      <div className="conn-grid">
        {renderBlock('IBM BPM', bpm, setBpm, 'ibm_bpm')}
        {renderBlock('FileNet', filenet, setFilenet, 'filenet')}
      </div>

      <div className="conn-actions">
        <button type="button" className="btn-secondary" onClick={load} disabled={saving}>
          Reload
        </button>
        <button type="button" className="btn-primary" onClick={save} disabled={saving}>
          {saving ? <Loader className="spinner" size={18} /> : <Save size={18} />}
          <span>Save &amp; apply pools</span>
        </button>
      </div>
    </div>
  );
}

export default ConnectionsSettings;
