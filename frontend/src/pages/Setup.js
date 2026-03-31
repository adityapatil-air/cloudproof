import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const REGIONS = [
  'us-east-1','us-east-2','us-west-1','us-west-2',
  'ap-south-1','ap-northeast-1','ap-southeast-1','ap-southeast-2',
  'eu-west-1','eu-central-1','ca-central-1','sa-east-1',
];

function authHeader() {
  const token = localStorage.getItem('cloudproof_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export default function Setup() {
  const navigate  = useNavigate();
  const user      = JSON.parse(localStorage.getItem('cloudproof_user') || '{}');
  const [step,    setStep]    = useState(1);  // 1 | 2 | 3
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  // Step 1 — AWS credentials
  const [creds, setCreds] = useState({ access_key: '', secret_key: '', region: 'us-east-1' });

  // Step 2 — Bucket selection
  const [buckets,    setBuckets]    = useState([]);
  const [selBucket,  setSelBucket]  = useState('');
  const [s3Prefix,   setS3Prefix]   = useState('');

  // Step 3 — Processing
  const [syncing,      setSyncing]      = useState(false);
  const [syncDone,     setSyncDone]     = useState(false);
  const [syncCount,    setSyncCount]    = useState(0);
  const [syncProgress, setSyncProgress] = useState(0);   // files done
  const [syncTotal,    setSyncTotal]    = useState(0);   // files total

  // ── Step 1: validate & save credentials ──────────────────────────────────
  const saveCredentials = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      await axios.post(
        `${API}/api/credentials`,
        { access_key: creds.access_key.trim(), secret_key: creds.secret_key.trim(), region: creds.region },
        { headers: authHeader() }
      );
      // Fetch bucket list
      const { data } = await axios.get(`${API}/api/buckets`, { headers: authHeader() });
      setBuckets(data.buckets || []);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to validate AWS credentials.');
    } finally {
      setLoading(false);
    }
  };

  // ── Step 2: save selected bucket ─────────────────────────────────────────
  const saveBucket = async (e) => {
    e.preventDefault();
    if (!selBucket) { setError('Please select a bucket.'); return; }
    setError(''); setLoading(true);
    try {
      await axios.post(
        `${API}/api/buckets/select`,
        { bucket: selBucket, s3_prefix: s3Prefix.trim() },
        { headers: authHeader() }
      );
      // Update stored user so has_bucket is true
      const updated = { ...user, has_bucket: true };
      localStorage.setItem('cloudproof_user', JSON.stringify(updated));
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save bucket.');
    } finally {
      setLoading(false);
    }
  };

  // ── Step 3: trigger log sync (async + polling) ───────────────────────────
  const runSync = async () => {
    setError(''); setSyncing(true); setSyncProgress(0); setSyncTotal(0);
    try {
      // Start async job
      const { data: startData } = await axios.post(`${API}/api/sync`, {}, { headers: authHeader() });
      const jobId = startData.job_id;

      // Poll every 2 seconds
      const poll = setInterval(async () => {
        try {
          const { data: status } = await axios.get(
            `${API}/api/sync/status/${jobId}`,
            { headers: authHeader() }
          );
          setSyncProgress(status.files_done || 0);
          setSyncTotal(status.files_total || 0);

          if (status.status === 'done') {
            clearInterval(poll);
            setSyncCount(status.records || 0);
            setSyncing(false);
            setSyncDone(true);
          } else if (status.status === 'error') {
            clearInterval(poll);
            setError(status.error || 'Sync failed. You can retry from your profile.');
            setSyncing(false);
            setSyncDone(true);
          }
        } catch {
          clearInterval(poll);
          setError('Lost connection to server during sync.');
          setSyncing(false);
          setSyncDone(true);
        }
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start sync.');
      setSyncing(false);
    }
  };

  const goToProfile = () => navigate(`/${user.username}`);

  const logout = () => {
    localStorage.removeItem('cloudproof_token');
    localStorage.removeItem('cloudproof_user');
    navigate('/login');
  };

  return (
    <div className="setup-page">
      {/* Header */}
      <nav className="setup-nav">
        <div className="logo-box">☁</div>
        <span className="setup-nav-title">CloudProof Setup</span>
        <button className="btn btn-ghost btn-sm" onClick={logout} style={{ marginLeft: 'auto' }}>
          Sign out
        </button>
      </nav>

      <div className="setup-body">
        {/* Step indicator */}
        <div className="setup-steps">
          {[
            { n: 1, label: 'AWS Credentials' },
            { n: 2, label: 'Select Bucket'   },
            { n: 3, label: 'Sync Logs'       },
          ].map(({ n, label }) => (
            <div key={n} className={`setup-step${step >= n ? ' done' : ''}${step === n ? ' current' : ''}`}>
              <div className="setup-step-num">{step > n ? '✓' : n}</div>
              <div className="setup-step-label">{label}</div>
              {n < 3 && <div className="setup-step-line" />}
            </div>
          ))}
        </div>

        {/* ── Step 1 ──────────────────────────────────────────────────────── */}
        {step === 1 && (
          <div className="setup-card">
            <div className="setup-card-title">Connect your AWS account</div>
            <div className="setup-card-desc">
              Enter your AWS Access Key and Secret Key. These are stored encrypted and only used to read your CloudTrail logs.
              <br /><br />
              <span className="setup-tip">
                💡 Go to <strong>AWS Console → IAM → Users → Security Credentials</strong> to create an access key.
                <br /><br />
                <strong>Minimum policy required:</strong> <code>AmazonS3ReadOnlyAccess</code>
                <br />
                Admin access or <code>AmazonS3FullAccess</code> also works — anything that includes S3 read permissions.
              </span>
            </div>

            <form onSubmit={saveCredentials}>
              <div className="fg">
                <label className="fl">AWS Access Key ID <span className="auth-req">*</span></label>
                <input
                  className="fi"
                  type="text"
                  placeholder="AKIAIOSFODNN7EXAMPLE"
                  value={creds.access_key}
                  onChange={e => setCreds(c => ({ ...c, access_key: e.target.value }))}
                  required
                  autoComplete="off"
                  spellCheck={false}
                />
              </div>

              <div className="fg">
                <label className="fl">AWS Secret Access Key <span className="auth-req">*</span></label>
                <input
                  className="fi"
                  type="password"
                  placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                  value={creds.secret_key}
                  onChange={e => setCreds(c => ({ ...c, secret_key: e.target.value }))}
                  required
                  autoComplete="new-password"
                />
              </div>

              <div className="fg">
                <label className="fl">AWS Region</label>
                <select className="fsel" value={creds.region} onChange={e => setCreds(c => ({ ...c, region: e.target.value }))}>
                  {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>

              {error && <div className="alert alert-error">{error}</div>}

              <button type="submit" className="btn btn-primary btn-lg" style={{ width: '100%', marginTop: 8 }} disabled={loading}>
                {loading ? <><span className="spinner" />Validating…</> : 'Validate & Continue →'}
              </button>
            </form>
          </div>
        )}

        {/* ── Step 2 ──────────────────────────────────────────────────────── */}
        {step === 2 && (
          <div className="setup-card">
            <div className="setup-card-title">Select your CloudTrail bucket</div>
            <div className="setup-card-desc">
              Choose the S3 bucket where CloudTrail delivers your logs.
              Don't see the right bucket? Check that CloudTrail logging is enabled in your AWS account.
            </div>

            <form onSubmit={saveBucket}>
              <div className="fg">
                <label className="fl">S3 Bucket <span className="auth-req">*</span></label>
                {buckets.length === 0 ? (
                  <div className="alert alert-info">No buckets found in your account. Create a CloudTrail bucket first.</div>
                ) : (
                  <select
                    className="fsel"
                    value={selBucket}
                    onChange={e => setSelBucket(e.target.value)}
                    required
                  >
                    <option value="">— Select a bucket —</option>
                    {buckets.map(b => <option key={b} value={b}>{b}</option>)}
                  </select>
                )}
              </div>

              <div className="fg">
                <label className="fl">S3 Prefix <span className="auth-optional">(optional)</span></label>
                <input
                  className="fi"
                  type="text"
                  placeholder="AWSLogs/123456789012/"
                  value={s3Prefix}
                  onChange={e => setS3Prefix(e.target.value)}
                />
                <div className="fhint">Folder path inside the bucket. Leave blank to scan the whole bucket.</div>
              </div>

              {error && <div className="alert alert-error">{error}</div>}

              <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
                <button type="button" className="btn btn-ghost" onClick={() => { setStep(1); setError(''); }}>
                  ← Back
                </button>
                <button type="submit" className="btn btn-primary btn-lg" style={{ flex: 1 }} disabled={loading || !selBucket}>
                  {loading ? <><span className="spinner" />Saving…</> : 'Save & Continue →'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* ── Step 3 ──────────────────────────────────────────────────────── */}
        {step === 3 && (
          <div className="setup-card" style={{ textAlign: 'center' }}>
            <div className="setup-card-title">Sync your AWS logs</div>

            {!syncDone ? (
              <>
                <div className="setup-card-desc">
                  CloudProof will read your CloudTrail logs from S3, score your activity,
                  and build your heatmap. Large buckets are processed in batches.
                </div>

                {syncing ? (
                  <div className="sync-progress-wrap">
                    <div className="sync-progress-label">
                      {syncTotal > 0
                        ? `Processing file ${syncProgress} of ${syncTotal}…`
                        : 'Counting log files…'}
                    </div>
                    <div className="sync-progress-track">
                      <div
                        className="sync-progress-bar"
                        style={{ width: syncTotal > 0 ? `${Math.round((syncProgress / syncTotal) * 100)}%` : '0%' }}
                      />
                    </div>
                    {syncTotal > 0 && (
                      <div className="sync-progress-pct">
                        {Math.round((syncProgress / syncTotal) * 100)}%
                      </div>
                    )}
                  </div>
                ) : (
                  <>
                    <button
                      className="btn btn-primary btn-lg"
                      style={{ marginTop: 24, width: '100%' }}
                      onClick={runSync}
                    >
                      ▶ Start Sync
                    </button>
                    <p style={{ marginTop: 12, color: 'var(--text-2)', fontSize: 13 }}>
                      You can also skip this and sync later from your profile.
                    </p>
                    <button className="btn btn-ghost" style={{ marginTop: 4 }} onClick={goToProfile}>
                      Skip → Go to profile
                    </button>
                  </>
                )}
              </>
            ) : (
              <>
                {error ? (
                  <div className="alert alert-error" style={{ textAlign: 'left', marginBottom: 20 }}>{error}</div>
                ) : (
                  <div className="setup-sync-done">
                    <div className="setup-sync-icon">✓</div>
                    <div className="setup-sync-count">{syncCount} records processed</div>
                    <div style={{ color: 'var(--text-2)', fontSize: 13 }}>
                      Your heatmap is ready!
                    </div>
                  </div>
                )}
                <button className="btn btn-primary btn-lg" style={{ marginTop: 24, width: '100%' }} onClick={goToProfile}>
                  View my profile →
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
