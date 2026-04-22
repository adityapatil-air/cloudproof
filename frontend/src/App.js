import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import CalendarHeatmap from 'react-calendar-heatmap';
import 'react-calendar-heatmap/dist/styles.css';
import axios from 'axios';
import Dashboard from './Dashboard';
import Visual from './Visual';
import Resources from './Resources';

/** Returns the logged-in user if they own this profile, else null. */
function getLoggedInOwner(username) {
  try {
    const token = localStorage.getItem('cloudproof_token');
    const user  = JSON.parse(localStorage.getItem('cloudproof_user') || 'null');
    if (token && user && user.username === username) return user;
  } catch (_) {}
  return null;
}

const API = process.env.REACT_APP_API_URL || '';
const IS_DEV = process.env.NODE_ENV === 'development';

const SVC_COLORS = [
  '#ff9900','#58a6ff','#3fb950','#bc8cff','#e3b341',
  '#f85149','#79c0ff','#56d364','#d2a8ff','#ffa657',
];

function ownerKey(username) { return `cloudproof_owner_${username}`; }
function isOwner(username)   { return localStorage.getItem(ownerKey(username)) === 'true'; }

// ── Tier helpers ────────────────────────────────────────────────────────────
const TIER_ORDER  = ['Beginner','Intermediate','Advanced','Expert','Elite'];
const TIER_SCORES = { Beginner:0, Intermediate:100, Advanced:500, Expert:1500, Elite:5000 };
function tierColor(tier) {
  return { Beginner:'#8b949e', Intermediate:'#58a6ff', Advanced:'#e3b341', Expert:'#ff9900', Elite:'#bc8cff' }[tier] || '#8b949e';
}
function nextTierName(tier) {
  const i = TIER_ORDER.indexOf(tier);
  return i >= 0 && i < TIER_ORDER.length - 1 ? TIER_ORDER[i+1] : null;
}

// ── Main component ──────────────────────────────────────────────────────────
export default function App({ username }) {
  const navigate = useNavigate();

  const [profile,  setProfile]  = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [tab,      setTab]      = useState('overview');
  const [year,     setYear]     = useState(new Date().getFullYear());

  // sync modal state
  const [showSync, setShowSync]       = useState(false);
  const [showTest, setShowTest]       = useState(false);
  const [pin,      setPin]            = useState('');
  const [syncing,  setSyncing]        = useState(false);
  const [syncResult, setSyncResult]   = useState(null);

  // toast
  const [toast, setToast] = useState('');

  const owner      = isOwner(username);
  const loggedInMe = getLoggedInOwner(username); // non-null if this IS the logged-in user
  const [lastSync, setLastSync] = useState(null);  // last sync timestamp

  const handleLogout = () => {
    localStorage.removeItem('cloudproof_token');
    localStorage.removeItem('cloudproof_user');
    navigate('/login');
  };

  // ── fetch profile ──────────────────────────────────────────────────────
  const fetchProfile = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const { data } = await axios.get(`${API}/api/profile/${username}`);
      setProfile(data);
    } catch (e) {
      if (e.response?.status === 404) setError('Profile not found.');
      else setError('Failed to load profile.');
    } finally {
      setLoading(false);
    }
  }, [username]);

  useEffect(() => {
    if (!username) { navigate('/'); return; }
    fetchProfile();
  }, [username, fetchProfile, navigate]);

  // ── sync handlers ──────────────────────────────────────────────────────
  const openSync = () => { setPin(''); setSyncResult(null); setShowSync(true); };
  const openTest = () => { setPin(''); setSyncResult(null); setShowTest(true); };
  const closeModal = () => { setShowSync(false); setShowTest(false); setPin(''); setSyncResult(null); };

  // JWT-based sync for logged-in users (incremental - only new logs)
  const doJwtSync = async () => {
    setSyncing(true);
    setSyncResult(null);
    const token = localStorage.getItem('cloudproof_token');
    try {
      // Start async sync job
      const { data: startData } = await axios.post(
        `${API}/api/sync`, {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const jobId = startData.job_id;

      // Poll until done
      const poll = setInterval(async () => {
        try {
          const { data: status } = await axios.get(
            `${API}/api/sync/status/${jobId}`,
            { headers: { Authorization: `Bearer ${token}` } }
          );
          if (status.status === 'done') {
            clearInterval(poll);
            setSyncResult({ ok: true, msg: `Sync complete! ${status.records} new records processed.` });
            setLastSync(new Date().toLocaleTimeString());
            setSyncing(false);
            await fetchProfile();
          } else if (status.status === 'error') {
            clearInterval(poll);
            setSyncResult({ ok: false, msg: status.error || 'Sync failed.' });
            setSyncing(false);
          }
        } catch {
          clearInterval(poll);
          setSyncResult({ ok: false, msg: 'Lost connection during sync.' });
          setSyncing(false);
        }
      }, 2000);
    } catch (e) {
      setSyncResult({ ok: false, msg: e.response?.data?.error || 'Failed to start sync.' });
      setSyncing(false);
    }
  };

  // Legacy sync-pin based sync
  const doSync = async (isTest) => {
    if (!pin.trim()) return;
    setSyncing(true);
    setSyncResult(null);
    const endpoint = isTest
      ? `${API}/api/profile/${username}/test-sync`
      : `${API}/api/profile/${username}/sync`;
    try {
      const { data } = await axios.post(endpoint, { sync_pin: pin });
      setSyncResult({ ok: true, msg: data.message });
      await fetchProfile();
    } catch (e) {
      setSyncResult({ ok: false, msg: e.response?.data?.error || 'Operation failed.' });
    } finally {
      setSyncing(false);
    }
  };

  // ── copy link ──────────────────────────────────────────────────────────
  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setToast('Profile link copied!');
    setTimeout(() => setToast(''), 3000);
  };

  // ── loading / error ────────────────────────────────────────────────────
  if (loading) return <SkeletonPage />;
  if (error)   return <ErrorPage msg={error} />;
  if (!profile) return null;

  const { user, heatmap = {}, services = {}, recent_actions = [], total_score = 0, streaks = {}, credibility = {} } = profile;

  // convert heatmap dict → array for CalendarHeatmap
  const heatmapArr = Object.entries(heatmap)
    .map(([date, score]) => ({ date, count: score }));

  const yearData = heatmapArr.filter(d => d.date?.startsWith(String(year)));
  const startDate = new Date(`${year}-01-01`);
  const endDate   = new Date(`${year}-12-31`);

  // available years from data + current year
  const years = [...new Set([new Date().getFullYear(), ...heatmapArr.map(d => Number(d.date?.split('-')[0]))])]
    .filter(Boolean).sort((a,b) => b - a);

  // convert services dict → sorted array
  const svcArr = Object.entries(services)
    .map(([service, score]) => ({ service, score }))
    .sort((a,b) => b.score - a.score);
  const maxSvc = svcArr.length ? svcArr[0].score : 1;

  // tier progress
  const tier = credibility.tier || 'Beginner';
  const tColor = tierColor(tier);
  const nextTier = nextTierName(tier);
  const prevScore = TIER_SCORES[tier] || 0;
  const nextScore = nextTier ? TIER_SCORES[nextTier] : null;
  const pct = nextScore ? Math.min(100, ((total_score - prevScore) / (nextScore - prevScore)) * 100) : 100;

  return (
    <div>
      {IS_DEV && <div className="dev-banner">⚠ Development Mode — test features active for profile owners</div>}

      {/* Setup nudge: shown when the logged-in user hasn't connected AWS yet */}
      {loggedInMe && !loggedInMe.has_bucket && (
        <div className="setup-banner">
          <span>☁ Connect your AWS account to start tracking activity.</span>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/setup')}>
            Complete Setup →
          </button>
        </div>
      )}

      {/* ── Navbar ──────────────────────────────────────────────────────── */}
      <nav className="navbar">
        <div className="navbar-inner">
          <a href="/" className="navbar-logo">
            <div className="logo-box">☁</div>
            CloudProof
          </a>

          <div className="navbar-tabs">
            {['overview','dashboard','visual','resources'].map(t => (
              <button
                key={t}
                className={`nav-tab${tab === t ? ' active' : ''}`}
                onClick={() => setTab(t)}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>

          <div className="navbar-actions">
            <button className="btn btn-ghost btn-sm" onClick={copyLink}>Share</button>
            {owner && IS_DEV && (
              <button className="btn btn-dev btn-sm" onClick={openTest}>
                Generate Test Logs
              </button>
            )}
            {/* JWT sync for logged-in owner */}
            {loggedInMe && (
              <button className="btn btn-primary btn-sm" onClick={doJwtSync} disabled={syncing}>
                {syncing ? <><span className="spinner" />Syncing…</> : 'Sync from AWS'}
              </button>
            )}
            {/* Legacy sync-pin for old profiles */}
            {owner && !loggedInMe && (
              <button className="btn btn-primary btn-sm" onClick={openSync} disabled={syncing}>
                {syncing ? <><span className="spinner" />Syncing…</> : 'Sync from AWS'}
              </button>
            )}
            {loggedInMe && (
              <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
                Sign out
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Sync result toast for JWT sync */}
      {syncResult && loggedInMe && (
        <div className={`alert alert-${syncResult.ok ? 'success' : 'error'}`}
          style={{margin:'8px 24px', borderRadius:8, cursor:'pointer'}}
          onClick={() => setSyncResult(null)}
        >
          {syncResult.msg} {lastSync && syncResult.ok && <span style={{opacity:0.6, fontSize:11}}>· {lastSync}</span>}
        </div>
      )}

      {/* ── Page ──────────────────────────────────────────────────────────── */}
      <div className="page">

        {/* Profile Hero */}
        <div className="profile-hero">
          <div className="profile-hero-top">
            <div className="avatar">
              {(user.name || username || '?')[0].toUpperCase()}
            </div>
            <div className="profile-details">
              <div className="profile-name">{user.name || username}</div>
              <div className="profile-handle">@{user.username || username}</div>
              <div className="profile-meta">
                <span className={`tier-badge tier-${tier}`}>{tier}</span>
                {user.created_at && (
                  <span className="meta-item">
                    📅 Joined {new Date(user.created_at).toLocaleDateString('en-US',{month:'short',year:'numeric'})}
                  </span>
                )}
              </div>
            </div>
          </div>

          {nextTier && (
            <div className="tier-progress">
              <div className="tier-progress-label">
                <span>Progress to {nextTier}</span>
                <span style={{fontFamily:'JetBrains Mono,monospace'}}>{total_score} / {nextScore} pts</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{width:`${pct}%`, background: tColor}} />
              </div>
            </div>
          )}

          <div className="divider" />

          <div className="stats-grid">
            <div className="stat-card score">
              <div className="stat-val">{total_score.toLocaleString()}</div>
              <div className="stat-lbl">Total Score</div>
            </div>
            <div className="stat-card streak">
              <div className="stat-val">{(streaks.current || 0) > 0 ? `${streaks.current}🔥` : 0}</div>
              <div className="stat-lbl">Current Streak</div>
            </div>
            <div className="stat-card best">
              <div className="stat-val">{streaks.longest || 0}</div>
              <div className="stat-lbl">Longest Streak</div>
            </div>
            <div className="stat-card services">
              <div className="stat-val">{svcArr.length}</div>
              <div className="stat-lbl">Services Used</div>
            </div>
          </div>
        </div>

        {/* ── Tab Content ─────────────────────────────────────────────────── */}
        {tab === 'overview' && (
          <Overview
            yearData={yearData}
            startDate={startDate}
            endDate={endDate}
            years={years}
            year={year}
            onYear={setYear}
            svcArr={svcArr}
            maxSvc={maxSvc}
            recent={recent_actions}
          />
        )}
        {tab === 'dashboard' && <Dashboard username={username} apiBase={API} />}
        {tab === 'visual'    && <Visual    username={username} apiBase={API} />}
        {tab === 'resources' && <Resources username={username} apiBase={API} />}
      </div>

      {/* ── Sync / Test Modal ──────────────────────────────────────────────── */}
      {(showSync || showTest) && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && closeModal()}>
          <div className="modal">
            {showTest ? (
              <>
                <div className="modal-title">Generate Test Logs</div>
                <div className="modal-desc">
                  Generates random CloudTrail-like events and feeds them through the scoring engine.
                  <br /><br />
                  <span style={{color:'var(--purple)',fontSize:'12px'}}>⚠ DEV ONLY — remove before production.</span>
                </div>
              </>
            ) : (
              <>
                <div className="modal-title">Sync from AWS S3</div>
                <div className="modal-desc">
                  Fetches new CloudTrail logs from your S3 bucket and updates your profile.
                  <br />Existing scores are never deleted — even if S3 logs are removed later.
                </div>
              </>
            )}

            <div className="fg">
              <label className="fl">Sync Password</label>
              <input
                className="fi"
                type="password"
                placeholder="Enter your sync password"
                value={pin}
                onChange={e => setPin(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && doSync(showTest)}
                autoFocus
              />
            </div>

            {syncResult && (
              <div className={`alert alert-${syncResult.ok ? 'success' : 'error'}`}>
                {syncResult.msg}
              </div>
            )}

            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={closeModal}>Cancel</button>
              <button
                className={`btn ${showTest ? 'btn-dev' : 'btn-primary'}`}
                onClick={() => doSync(showTest)}
                disabled={syncing || !pin.trim()}
              >
                {syncing
                  ? <><span className="spinner" />Processing…</>
                  : showTest ? 'Generate & Process' : 'Start Sync'
                }
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

// ── Overview Tab ─────────────────────────────────────────────────────────────
function Overview({ yearData, startDate, endDate, years, year, onYear, svcArr, maxSvc, recent }) {
  return (
    <>
      {/* Heatmap */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Activity Heatmap</span>
          <div className="year-row">
            {years.map(y => (
              <button key={y} className={`year-btn${year === y ? ' active' : ''}`} onClick={() => onYear(y)}>
                {y}
              </button>
            ))}
          </div>
        </div>
        <div className="heatmap-wrap">
          <CalendarHeatmap
            startDate={startDate}
            endDate={endDate}
            values={yearData}
            classForValue={v => {
              if (!v || !v.count) return 'color-empty';
              if (v.count < 20) return 'color-scale-1';
              if (v.count < 50) return 'color-scale-2';
              if (v.count < 80) return 'color-scale-3';
              return 'color-scale-4';
            }}
            showWeekdayLabels
            titleForValue={v => v?.date ? `${v.date}: ${v.count||0} pts` : ''}
          />
        </div>
        <div className="heatmap-legend">
          <span>Less</span>
          {['var(--surface2)','var(--green-1)','var(--green-2)','var(--green-3)','var(--green-4)'].map((c,i) => (
            <div key={i} className="legend-cell" style={{background:c}} />
          ))}
          <span>More</span>
        </div>
      </div>

      <div className="two-col">
        {/* Service Breakdown */}
        <div className="card">
          <div className="card-header"><span className="card-title">Service Usage</span></div>
          {svcArr.length === 0 ? (
            <Empty ico="📊" ttl="No service data" desc="Sync your AWS logs to see service breakdown." />
          ) : (
            <div className="svc-list">
              {svcArr.slice(0,10).map((s,i) => (
                <div key={s.service} className="svc-row">
                  <div className="svc-row-top">
                    <div className="svc-name">
                      <div className="svc-dot" style={{background: SVC_COLORS[i % SVC_COLORS.length]}} />
                      {s.service}
                    </div>
                    <div className="svc-score">{s.score} pts</div>
                  </div>
                  <div className="svc-track">
                    <div className="svc-fill" style={{
                      width: `${(s.score / maxSvc) * 100}%`,
                      background: SVC_COLORS[i % SVC_COLORS.length],
                    }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="card-header"><span className="card-title">Recent Activity</span></div>
          {recent.length === 0 ? (
            <Empty ico="⚡" ttl="No activity yet" desc="Your AWS actions appear here after syncing." />
          ) : (
            <table className="act-table">
              <thead>
                <tr><th>Date</th><th>Service</th><th>Action</th><th>Pts</th></tr>
              </thead>
              <tbody>
                {recent.slice(0,10).map((a,i) => (
                  <tr key={i}>
                    <td style={{color:'var(--text-2)',fontSize:'11px'}} className="mono">{a.date}</td>
                    <td><span className="tag-svc">{a.service}</span></td>
                    <td className="mono" style={{fontSize:'11px'}}>{a.action}</td>
                    <td><span className="pill-score">+{a.score}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}

// ── Shared helpers ────────────────────────────────────────────────────────────
function Empty({ ico, ttl, desc }) {
  return (
    <div className="empty">
      <div className="empty-ico">{ico}</div>
      <div className="empty-ttl">{ttl}</div>
      <div className="empty-desc">{desc}</div>
    </div>
  );
}

function SkeletonPage() {
  return (
    <div>
      <nav className="navbar">
        <div className="navbar-inner">
          <div className="navbar-logo"><div className="logo-box">☁</div>CloudProof</div>
        </div>
      </nav>
      <div className="page">
        <div className="skel-hero">
          <div style={{display:'flex',gap:16,marginBottom:22}}>
            <div className="skel" style={{width:68,height:68,borderRadius:'50%'}} />
            <div style={{flex:1,display:'flex',flexDirection:'column',gap:8}}>
              <div className="skel" style={{height:18,width:160}} />
              <div className="skel" style={{height:13,width:110}} />
              <div className="skel" style={{height:20,width:90,borderRadius:20}} />
            </div>
          </div>
          <div className="stats-grid">
            {[1,2,3,4].map(i=>(
              <div key={i} className="stat-card">
                <div className="skel" style={{height:26,marginBottom:8}} />
                <div className="skel" style={{height:11,width:'55%',margin:'0 auto'}} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ErrorPage({ msg }) {
  return (
    <div>
      <nav className="navbar">
        <div className="navbar-inner">
          <a href="/" className="navbar-logo"><div className="logo-box">☁</div>CloudProof</a>
        </div>
      </nav>
      <div className="err-page">
        <div style={{fontSize:44}}>☁</div>
        <div style={{fontSize:18,fontWeight:600}}>Profile not found</div>
        <div style={{fontSize:13,color:'var(--text-2)'}}>{msg}</div>
        <a href="/" className="btn btn-primary" style={{marginTop:8}}>Create a Profile</a>
      </div>
    </div>
  );
}
