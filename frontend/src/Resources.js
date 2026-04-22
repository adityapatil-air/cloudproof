import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RES_ICONS = {
  EC2_INSTANCE:'🖥', VPC:'🌐', SUBNET:'📡', ROUTE_TABLE:'🗺',
  INTERNET_GATEWAY:'🌍', S3_BUCKET:'🪣', IAM_ROLE:'🔑', IAM_USER:'👤',
  IAM_POLICY_ATTACHMENT:'📎', LAMBDA_FUNCTION:'λ', RDS_INSTANCE:'🗄',
  CFN_STACK:'🏗', EKS_CLUSTER:'⎈', ECS_CLUSTER:'📦',
};
const RES_COLORS = {
  EC2_INSTANCE:'#ff9900', S3_BUCKET:'#58a6ff', IAM_ROLE:'#f85149',
  LAMBDA_FUNCTION:'#3fb950', RDS_INSTANCE:'#e3b341', EKS_CLUSTER:'#bc8cff',
  ECS_CLUSTER:'#ffa657', VPC:'#6e7681',
};

function resIcon(type)  { return RES_ICONS[type]  || '📦'; }
function resColor(type) { return RES_COLORS[type] || '#484f58'; }

function stateClass(state = '') {
  const s = state.toLowerCase();
  if (/running|active|available|attached/.test(s)) return 's-running';
  if (/stop/.test(s))                              return 's-stopped';
  if (/terminat|delet/.test(s))                    return 's-terminated';
  if (/creat|pending/.test(s))                     return 's-pending';
  return 's-unknown';
}

const ACTIVE_STATES     = ['running','active','available','attached','creating','pending'];
const TERMINATED_STATES = ['terminated','deleted','deleting'];

export default function Resources({ username, apiBase }) {
  const API = apiBase || process.env.REACT_APP_API_URL || '';
  const [resources, setResources] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState('');
  const [filter,    setFilter]    = useState('all');

  useEffect(() => {
    if (!username) return;
    setLoading(true);
    axios.get(`${API}/api/profile/${username}/resources`)
      .then(({ data }) => { setResources(data.resources || []); setError(''); })
      .catch(() => setError('Failed to load resources.'))
      .finally(() => setLoading(false));
  }, [username, API]);

  if (loading) return (
    <div className="card">
      {[1,2,3,4].map(i=><div key={i} className="skel" style={{height:46,marginBottom:6}}/>)}
    </div>
  );

  if (error) return <div className="card"><div className="alert alert-error">{error}</div></div>;

  if (resources.length === 0) return (
    <div className="card">
      <div className="empty">
        <div className="empty-ico">🏗</div>
        <div className="empty-ttl">No resources tracked</div>
        <div className="empty-desc">AWS resources you create will appear here after syncing your logs.</div>
      </div>
    </div>
  );

  // Build parent → children map
  const parentMap = {};
  const childMap  = {};
  resources.forEach(r => {
    if (!r.parent_resource_id) {
      parentMap[r.resource_id] = { ...r, children: [] };
    } else {
      childMap[r.parent_resource_id] = childMap[r.parent_resource_id] || [];
      childMap[r.parent_resource_id].push(r);
    }
  });
  Object.keys(childMap).forEach(pid => {
    if (parentMap[pid]) parentMap[pid].children = childMap[pid];
    else childMap[pid].forEach(c => { parentMap[c.resource_id] = { ...c, children: [] }; });
  });

  // Filter
  const allItems = Object.values(parentMap);
  const filtered = allItems.filter(r => {
    const s = (r.state || '').toLowerCase();
    if (filter === 'active')     return ACTIVE_STATES.some(x => s.includes(x));
    if (filter === 'terminated') return TERMINATED_STATES.some(x => s.includes(x));
    return true;
  }).map(r => ({
    ...r,
    children: (r.children || []).filter(c => {
      const s = (c.state || '').toLowerCase();
      if (filter === 'active')     return ACTIVE_STATES.some(x => s.includes(x));
      if (filter === 'terminated') return TERMINATED_STATES.some(x => s.includes(x));
      return true;
    }),
  }));

  // Group by resource type for section headers
  const grouped = filtered.reduce((acc, r) => {
    const key = r.resource_type || 'Other';
    acc[key] = acc[key] || [];
    acc[key].push(r);
    return acc;
  }, {});

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Resource Inventory</span>
        <div className="filter-bar">
          {['all','active','terminated'].map(f => (
            <button key={f} className={`filter-btn${filter===f?' active':''}`} onClick={()=>setFilter(f)}>
              {f.charAt(0).toUpperCase()+f.slice(1)}
              {f === 'all' && ` (${resources.length})`}
            </button>
          ))}
        </div>
      </div>

      {Object.entries(grouped).map(([type, items]) => (
        <div key={type} className="res-group">
          <div className="res-group-title">
            {resIcon(type)} {type.replace(/_/g,' ')} ({items.length})
          </div>

          {items.map(r => (
            <div key={r.resource_id}>
              <div className="res-item">
                <div className="res-ico" style={{background:`${resColor(r.resource_type)}20`}}>
                  {resIcon(r.resource_type)}
                </div>
                <div className="res-info">
                  <div className="res-id">{r.resource_id}</div>
                  <div className="res-type">{r.resource_type?.replace(/_/g,' ')}</div>
                </div>
                {r.state && (
                  <span className={`state-pill ${stateClass(r.state)}`}>● {r.state}</span>
                )}
              </div>

              {(r.children||[]).length > 0 && (
                <div className="res-children">
                  {r.children.map(c => (
                    <div key={c.resource_id} className="res-child">
                      <span style={{fontSize:13}}>{resIcon(c.resource_type)}</span>
                      <div style={{flex:1,minWidth:0}}>
                        <div className="res-id" style={{fontSize:11}}>{c.resource_id}</div>
                        <div className="res-type">{c.resource_type?.replace(/_/g,' ')}</div>
                      </div>
                      {c.state && (
                        <span className={`state-pill ${stateClass(c.state)}`}>● {c.state}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
