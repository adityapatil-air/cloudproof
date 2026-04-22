import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SVC_COLORS = {
  EC2:'#ff9900', S3:'#58a6ff', IAM:'#f85149', LAMBDA:'#3fb950',
  RDS:'#e3b341', EKS:'#bc8cff', ECS:'#ffa657', CLOUDFORMATION:'#79c0ff',
  DYNAMODB:'#56d364', ROUTE53:'#d2a8ff', VPC:'#6e7681',
};
function svcColor(s) { return SVC_COLORS[s?.toUpperCase()] || '#8b949e'; }

function actionIcon(name = '') {
  if (/create|launch|start|run|put|attach/i.test(name)) return '＋';
  if (/delete|terminate|remove|detach/i.test(name))     return '−';
  if (/update|modify|change|set/i.test(name))           return '✎';
  if (/stop|disable/i.test(name))                       return '■';
  return '○';
}

export default function Visual({ username, apiBase }) {
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
      .catch(() => setError('Failed to load visual data.'))
      .finally(() => setLoading(false));
  }, [username, filter, API]);

  if (loading) return (
    <div className="card">
      {[1,2,3,4].map(i=><div key={i} className="skel" style={{height:56,marginBottom:8}}/>)}
    </div>
  );

  if (error) return <div className="card"><div className="alert alert-error">{error}</div></div>;

  if (days.length === 0) return (
    <div className="card">
      <div className="empty">
        <div className="empty-ico">📈</div>
        <div className="empty-ttl">No visual data yet</div>
        <div className="empty-desc">After syncing, you'll see a visual service-activity timeline here.</div>
      </div>
    </div>
  );

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Service Activity Timeline</span>
        <div className="filter-bar">
          {[7,30,90].map(n=>(
            <button key={n} className={`filter-btn${filter===n?' active':''}`} onClick={()=>setFilter(n)}>
              {n}d
            </button>
          ))}
        </div>
      </div>

      {days.map(day => {
        // aggregate services: {name, count, score, actions[]}
        const svcs = Object.entries(day.services || {}).map(([name, d]) => ({
          name,
          count: d.count,
          score: d.total_score,
          actions: d.actions || [],
        }));

        // flatten & aggregate action names per service
        const svcActionMap = {};
        svcs.forEach(s => {
          const agg = {};
          s.actions.forEach(a => { agg[a.action] = (agg[a.action]||0)+1; });
          svcActionMap[s.name] = agg;
        });

        return (
          <div key={day.date} className="vis-day">
            <div className="vis-day-hd">
              <span style={{fontSize:12,fontWeight:600,fontFamily:'JetBrains Mono,monospace',color:'var(--text)'}}>
                {day.date}
              </span>
              <span style={{fontSize:11,color:'var(--text-2)'}}>
                {day.total_actions} actions · {day.total_score} pts
              </span>
            </div>

            <div className="vis-chips">
              {svcs.map(s => (
                <div
                  key={s.name}
                  className="vis-chip"
                  style={{borderColor: svcColor(s.name), color: svcColor(s.name)}}
                  title={Object.entries(svcActionMap[s.name]||{}).map(([a,c])=>`${a} ×${c}`).join(', ')}
                >
                  {s.name}
                  <span className="chip-cnt">{s.count}</span>
                </div>
              ))}
            </div>

            {/* expanded action list per service */}
            {svcs.map(s => (
              <div key={s.name} className="vis-actions-list">
                {Object.entries(svcActionMap[s.name]||{}).map(([act, cnt]) => (
                  <div key={act} className="vis-action-row">
                    <span style={{color:svcColor(s.name),fontWeight:700,fontSize:12,minWidth:16}}>{actionIcon(act)}</span>
                    <span style={{fontFamily:'JetBrains Mono,monospace',flex:1,fontSize:11}}>{act}</span>
                    {cnt > 1 && <span style={{color:'var(--text-3)',fontSize:11}}>×{cnt}</span>}
                    <span style={{color:'var(--text-3)',fontSize:11,fontFamily:'JetBrains Mono,monospace',marginLeft:8}}>{s.name}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
