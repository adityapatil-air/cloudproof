import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || '';

const REGIONS = [
  'us-east-1','us-east-2','us-west-1','us-west-2',
  'ap-south-1','ap-northeast-1','ap-southeast-1','ap-southeast-2',
  'eu-west-1','eu-central-1','ca-central-1','sa-east-1',
];

export default function Auth() {
  const navigate     = useNavigate();
  const [params]     = useSearchParams();
  const [mode, setMode]   = useState('login'); // 'login' | 'signup' | 'forgot'
  const [step, setStep]   = useState(1);       // signup: 1=basic info, 2=aws keys
  const [form, setForm]   = useState({ username: '', name: '', email: '', password: '', confirm: '' });
  const [aws,  setAws]    = useState({ access_key: '', secret_key: '', region: 'ap-south-1' });
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');
  const [info,    setInfo]    = useState('');
  const [showPwd, setShowPwd] = useState(false);

  useEffect(() => {
    const oauthError = params.get('error');
    if (oauthError) setError(decodeURIComponent(oauthError));
  }, [params]);

  const set        = (k, v) => { setForm(f => ({ ...f, [k]: v })); setError(''); };
  const setAwsKey  = (k, v) => { setAws(a  => ({ ...a, [k]: v })); setError(''); };
  const switchMode = (m)    => { setMode(m); setStep(1); setError(''); setInfo(''); };

  const oauthLogin = (provider) => {
    window.location.href = `${API}/api/auth/${provider}`;
  };

  const _storeAndRedirect = (data) => {
    localStorage.setItem('cloudproof_token', data.token);
    localStorage.setItem('cloudproof_user',  JSON.stringify(data.user));
    if (!data.user.has_bucket) navigate('/setup');
    else                       navigate(`/${data.user.username}`);
  };

  // ── Signup Step 1: validate username/email (no account created yet) ────────
  const handleBasicInfo = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) { setError('Passwords do not match.'); return; }
    if (form.password.length < 8)       { setError('Password must be at least 8 characters.'); return; }
    setError(''); setLoading(true);
    try {
      await axios.post(`${API}/api/auth/preflight`, {
        username: form.username.trim().toLowerCase(),
        email:    form.email.trim().toLowerCase(),
        password: form.password,
      });
      setStep(2); // Move to AWS keys step
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  // ── Signup Step 2: verify AWS keys + create account ────────────────────────
  const handleAwsKeys = async (e) => {
    e.preventDefault();
    if (!aws.access_key || !aws.secret_key) { setError('Both AWS keys are required.'); return; }
    setError(''); setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/auth/signup`, {
        username:   form.username.trim().toLowerCase(),
        name:       form.name.trim() || form.username.trim(),
        email:      form.email.trim().toLowerCase(),
        password:   form.password,
        access_key: aws.access_key.trim(),
        secret_key: aws.secret_key.trim(),
        region:     aws.region,
      });
      _storeAndRedirect(data);
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  // ── Login ──────────────────────────────────────────────────────────────────
  const handleLogin = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/auth/login`, {
        email:    form.email.trim().toLowerCase(),
        password: form.password,
      });
      _storeAndRedirect(data);
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // ── Forgot password ────────────────────────────────────────────────────────
  const handleForgot = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      await axios.post(`${API}/api/auth/forgot-password`, { email: form.email.trim().toLowerCase() });
      setInfo('If that email is registered, a reset link has been sent. Check your inbox.');
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="auth-page">
      <div className="auth-logo">
        <div className="logo-box">☁</div>
        <h1>CloudProof</h1>
        <p>Verified AWS Cloud Activity Tracker</p>
      </div>

      <div className="auth-card">
        {mode !== 'forgot' && (
          <div className="auth-tabs">
            <button className={`auth-tab${mode === 'login'  ? ' active' : ''}`} onClick={() => switchMode('login')}>
              Sign in
            </button>
            <button className={`auth-tab${mode === 'signup' ? ' active' : ''}`} onClick={() => switchMode('signup')}>
              Create account
            </button>
          </div>
        )}

        <div className="auth-body">

          {/* ── Forgot password ───────────────────────────────────────────── */}
          {mode === 'forgot' && (
            <>
              <div className="auth-back" onClick={() => switchMode('login')}>← Back to sign in</div>
              <h2 className="auth-section-title">Reset your password</h2>
              <p className="auth-section-desc">Enter your email and we'll send you a reset link.</p>
              <form onSubmit={handleForgot} className="auth-form">
                <div className="auth-field">
                  <label>Email</label>
                  <input type="email" value={form.email} onChange={e => set('email', e.target.value)}
                    placeholder="you@example.com" required autoFocus />
                </div>
                {error && <div className="auth-error">{error}</div>}
                {info  && <div className="auth-success">{info}</div>}
                <button type="submit" className="auth-submit" disabled={loading}>
                  {loading ? 'Sending…' : 'Send reset link →'}
                </button>
              </form>
            </>
          )}

          {/* ── Login ─────────────────────────────────────────────────────── */}
          {mode === 'login' && (
            <>
              <div className="oauth-buttons">
                <button className="oauth-btn oauth-github" onClick={() => oauthLogin('github')}>
                  <svg height="18" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                  </svg>
                  Continue with GitHub
                </button>
                <button className="oauth-btn oauth-google" onClick={() => oauthLogin('google')}>
                  <svg viewBox="0 0 24 24" height="18">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continue with Google
                </button>
              </div>
              <div className="auth-divider"><span>or continue with email</span></div>
              <form onSubmit={handleLogin} className="auth-form">
                <div className="auth-field">
                  <label>Email <span className="req">*</span></label>
                  <input type="email" value={form.email} onChange={e => set('email', e.target.value)}
                    placeholder="you@example.com" required autoComplete="email" />
                </div>
                <div className="auth-field">
                  <label>Password <span className="req">*</span></label>
                  <div className="auth-pwd-wrap">
                    <input
                      type={showPwd ? 'text' : 'password'}
                      value={form.password} onChange={e => set('password', e.target.value)}
                      placeholder="Your password" required autoComplete="current-password"
                    />
                    <button type="button" className="auth-pwd-toggle" onClick={() => setShowPwd(v => !v)}>
                      {showPwd ? '🙈' : '👁'}
                    </button>
                  </div>
                </div>
                <div className="auth-forgot-row">
                  <button type="button" className="auth-link" onClick={() => switchMode('forgot')}>
                    Forgot password?
                  </button>
                </div>
                {error && <div className="auth-error">{error}</div>}
                <button type="submit" className="auth-submit" disabled={loading}>
                  {loading ? 'Signing in…' : 'Sign in →'}
                </button>
              </form>
            </>
          )}

          {/* ── Signup Step 1: Basic Info ──────────────────────────────────── */}
          {mode === 'signup' && step === 1 && (
            <>
              <div className="oauth-buttons">
                <button className="oauth-btn oauth-github" onClick={() => oauthLogin('github')}>
                  <svg height="18" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                  </svg>
                  Continue with GitHub
                </button>
                <button className="oauth-btn oauth-google" onClick={() => oauthLogin('google')}>
                  <svg viewBox="0 0 24 24" height="18">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continue with Google
                </button>
              </div>
              <div className="auth-divider"><span>or continue with email</span></div>
              <form onSubmit={handleBasicInfo} className="auth-form">
                <div className="auth-field">
                  <label>Username <span className="req">*</span></label>
                  <div className="auth-username-wrap">
                    <span className="auth-host">{window.location.host}/</span>
                    <input
                      type="text" value={form.username}
                      onChange={e => set('username', e.target.value.toLowerCase())}
                      placeholder="your-username" required
                      pattern="[a-z0-9_\-]{3,30}"
                      title="3–30 chars: lowercase letters, numbers, - _"
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
                  <input type="text" value={form.name} onChange={e => set('name', e.target.value)} placeholder="John Doe" />
                </div>
                <div className="auth-field">
                  <label>Email <span className="req">*</span></label>
                  <input type="email" value={form.email} onChange={e => set('email', e.target.value)}
                    placeholder="you@example.com" required autoComplete="email" />
                </div>
                <div className="auth-field">
                  <label>Password <span className="req">*</span> <span className="auth-optional">(min 8 chars)</span></label>
                  <div className="auth-pwd-wrap">
                    <input
                      type={showPwd ? 'text' : 'password'}
                      value={form.password} onChange={e => set('password', e.target.value)}
                      placeholder="Create a password" required minLength={8} autoComplete="new-password"
                    />
                    <button type="button" className="auth-pwd-toggle" onClick={() => setShowPwd(v => !v)}>
                      {showPwd ? '🙈' : '👁'}
                    </button>
                  </div>
                </div>
                <div className="auth-field">
                  <label>Confirm password <span className="req">*</span></label>
                  <input type="password" value={form.confirm} onChange={e => set('confirm', e.target.value)}
                    placeholder="Repeat your password" required autoComplete="new-password" />
                  {form.confirm && form.confirm !== form.password && (
                    <p className="auth-field-err">Passwords don't match.</p>
                  )}
                </div>
                {error && <div className="auth-error">{error}</div>}
                <button type="submit" className="auth-submit" disabled={loading}>
                  {loading ? 'Checking…' : 'Continue →'}
                </button>
              </form>
            </>
          )}

          {/* ── Signup Step 2: AWS Keys (account created only after this) ──── */}
          {mode === 'signup' && step === 2 && (
            <>
              <div className="auth-back" onClick={() => { setStep(1); setError(''); }}>← Back</div>
              <div style={{ marginBottom: 16, fontSize: 13, color: 'var(--text-2)' }}>
                Connect your AWS account to verify your activity. Your account is created only after this step.
              </div>
              <form onSubmit={handleAwsKeys} className="auth-form">
                <div className="auth-field">
                  <label>AWS Access Key ID <span className="req">*</span></label>
                  <input
                    className="fi" type="text" placeholder="AKIAIOSFODNN7EXAMPLE"
                    value={aws.access_key} onChange={e => setAwsKey('access_key', e.target.value)}
                    required autoComplete="off" spellCheck={false}
                  />
                </div>
                <div className="auth-field">
                  <label>AWS Secret Access Key <span className="req">*</span></label>
                  <input
                    className="fi" type="password" placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                    value={aws.secret_key} onChange={e => setAwsKey('secret_key', e.target.value)}
                    required autoComplete="new-password"
                  />
                </div>
                <div className="auth-field">
                  <label>AWS Region</label>
                  <select className="fsel" value={aws.region} onChange={e => setAwsKey('region', e.target.value)}>
                    {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                {error && <div className="auth-error">{error}</div>}
                <button type="submit" className="auth-submit" disabled={loading}>
                  {loading ? 'Verifying & Creating Account…' : 'Create Account →'}
                </button>
              </form>
            </>
          )}

        </div>
      </div>

      <p className="auth-footer">
        {mode === 'login'  && <>No account? <button className="auth-link" onClick={() => switchMode('signup')}>Create one free</button></>}
        {mode === 'signup' && <>Already have an account? <button className="auth-link" onClick={() => switchMode('login')}>Sign in</button></>}
      </p>
    </div>
  );
}
