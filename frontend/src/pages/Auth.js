import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Auth() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [form, setForm] = useState({ username: '', name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');
  const [success, setSuccess] = useState('');

  const set = (k, v) => { setForm(f => ({ ...f, [k]: v })); setError(''); };

  const switchMode = (m) => { setMode(m); setError(''); setSuccess(''); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setSuccess(''); setLoading(true);
    try {
      if (mode === 'signup') {
        const { data } = await axios.post(`${API}/api/auth/signup`, {
          username: form.username.trim().toLowerCase(),
          name:     form.name.trim() || form.username.trim(),
          email:    form.email.trim().toLowerCase(),
          password: form.password,
        });
        localStorage.setItem('cloudproof_token', data.token);
        localStorage.setItem('cloudproof_user',  JSON.stringify(data.user));
        setSuccess('Account created! Redirecting to setup…');
        setTimeout(() => navigate('/setup'), 700);
      } else {
        const { data } = await axios.post(`${API}/api/auth/login`, {
          email:    form.email.trim().toLowerCase(),
          password: form.password,
        });
        localStorage.setItem('cloudproof_token', data.token);
        localStorage.setItem('cloudproof_user',  JSON.stringify(data.user));
        // If bucket not configured yet → go to setup, else → profile
        if (!data.user.has_bucket) {
          navigate('/setup');
        } else {
          navigate(`/${data.user.username}`);
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-logo">
        <div className="logo-box">☁</div>
        <h1>CloudProof</h1>
        <p>Verified AWS Activity Tracker</p>
      </div>

      <div className="auth-card">
        {/* Tabs */}
        <div className="auth-tabs">
          <button className={`auth-tab${mode === 'login'  ? ' active' : ''}`} onClick={() => switchMode('login')}>
            Sign in
          </button>
          <button className={`auth-tab${mode === 'signup' ? ' active' : ''}`} onClick={() => switchMode('signup')}>
            Create account
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <>
              <div className="auth-field">
                <label>Username <span className="auth-req">*</span></label>
                <div className="auth-username-wrap">
                  <span className="auth-host">{window.location.host}/</span>
                  <input
                    type="text"
                    value={form.username}
                    onChange={e => set('username', e.target.value.toLowerCase())}
                    placeholder="your-username"
                    required
                    pattern="[a-z0-9_\-]{3,30}"
                    title="3–30 chars: lowercase letters, numbers, hyphens, underscores"
                  />
                </div>
                {form.username && (
                  <p className="auth-hint">
                    Public profile: <span className="auth-url">{window.location.host}/{form.username}</span>
                  </p>
                )}
              </div>

              <div className="auth-field">
                <label>Display name <span className="auth-optional">(optional)</span></label>
                <input
                  type="text"
                  value={form.name}
                  onChange={e => set('name', e.target.value)}
                  placeholder="John Doe"
                />
              </div>
            </>
          )}

          <div className="auth-field">
            <label>Email <span className="auth-req">*</span></label>
            <input
              type="email"
              value={form.email}
              onChange={e => set('email', e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="auth-field">
            <label>Password <span className="auth-req">*</span></label>
            <input
              type="password"
              value={form.password}
              onChange={e => set('password', e.target.value)}
              placeholder={mode === 'signup' ? 'At least 8 characters' : 'Your password'}
              required
              minLength={mode === 'signup' ? 8 : 1}
              autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
            />
          </div>

          {error   && <div className="auth-error">{error}</div>}
          {success && <div className="auth-success">{success}</div>}

          <button type="submit" className="auth-submit" disabled={loading}>
            {loading
              ? (mode === 'signup' ? 'Creating…' : 'Signing in…')
              : (mode === 'signup' ? 'Create account →' : 'Sign in →')}
          </button>
        </form>
      </div>

      <p className="auth-footer">
        {mode === 'login'
          ? <>No account? <button className="auth-link" onClick={() => switchMode('signup')}>Create one</button></>
          : <>Already have one? <button className="auth-link" onClick={() => switchMode('login')}>Sign in</button></>
        }
      </p>
    </div>
  );
}
