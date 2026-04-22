import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SVC_COLORS = {
  EC2:'#ff9900', S3:'#58a6ff', IAM:'#f85149', LAMBDA:'#3fb950',
  RDS:'#e3b341', EKS:'#bc8cff', ECS:'#ffa657', CLOUDFORMATION:'#79c0ff',
  DYNAMODB:'#56d364', ROUTE53:'#d2a8ff', VPC:'#6e7681',
};
function svcColor(s) { return SVC_COLORS[s?.toUpperCase()] || '#8b949e'; }

function formatTime(ts) {
  if (!ts) return '—';
  try { return new Date(ts).toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit' }); }
  catch { return '—'; }
}

export default function Dashboard({ username, apiBase }) {
  const API = apiBase || process.env.REACT_APP_API_URL || '';
  const [days,    setDays]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [filter,  setFilter]  = useState(30);

  useEffect(() => {
    if (!username) return;
    setLoading(true);
    axios.get(`${API}/api/profile/${username}/dashboard?days=${filter}`)
      .then(({ data }) => { setDays(data.dashboard || []); setError(''); })
      .catch(() => setError('Failed to load dashboard.'))
      .finally(() => setLoading(false));
  }, [username, filter, API]);

  if (loading) return (
    <div className="card">
      {[1,2,3].map(i=><div key={i} className="skel" style={{height:80,marginBottom:10}}/>)}
    </div>
  );

  if (error) return <div className="card"><div className="alert alert-error">{error}</div></div>;

  if (days.length === 0) return (
    <div className="card">
      <div className="empty">
        <div className="empty-ico">📅</div>
        <div className="empty-ttl">No daily data yet</div>
        <div className="empty-desc">Sync your AWS logs to see a day-by-day activity breakdown.</div>
      </div>
    </div>
  );

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Daily Activity Breakdown</span>
        <div className="filter-bar">
          {[7,30,90].map(n=>(
            <button key={n} className={`filter-btn${filter===n?' active':''}`} onClick={()=>setFilter(n)}>
              {n}d
            </button>
          ))}
        </div>
      </div>

      {days.map(day => (
        <div key={day.date} className="day-card">
          <div className="day-card-hd">
            <span className="day-date">
              {new Date(day.date+'T00:00:00').toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'})}
            </span>
            <span className="day-pts">+{day.total_score} pts · {day.total_actions} actions</span>
          </div>

          {Object.entries(day.services || {}).map(([svc, data]) => (
            <div key={svc} className="svc-section">
              <div className="svc-hd">
                <span
                  className="svc-badge"
                  style={{ color: svcColor(svc), borderLeftColor: svcColor(svc) }}
                >
                  {svc}
                </span>
                <span className="svc-badge-stats">{data.count} actions · {data.total_score} pts</span>
              </div>
              <div className="action-rows">
                {(data.actions || []).map((a, i) => (
                  <div key={i} className="action-row">
                    <span className="action-time">{formatTime(a.timestamp)}</span>
                    <span className="action-name">{a.action}</span>
                    <span className="action-pts">+{a.score}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
