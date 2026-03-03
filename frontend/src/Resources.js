import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Resources({ userId }) {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchResources();
  }, [userId]);

  const fetchResources = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:5000/api/users/${userId}/resources`);
      setResources(response.data.resources);
    } catch (error) {
      console.error('Error fetching resources:', error);
    } finally {
      setLoading(false);
    }
  };

  const getResourceIcon = (type) => {
    const icons = {
      'EC2_INSTANCE': '🖥️',
      'VPC': '🌐',
      'SUBNET': '📡',
      'ROUTE_TABLE': '🗺️',
      'INTERNET_GATEWAY': '🌍',
      'S3_BUCKET': '🪣',
      'IAM_ROLE': '🔐',
      'IAM_USER': '👤',
      'IAM_POLICY_ATTACHMENT': '📎',
      'LAMBDA_FUNCTION': '⚡',
      'RDS_INSTANCE': '🗄️',
      'CFN_STACK': '📚',
      'EKS_CLUSTER': '☸️',
    };
    return icons[type] || '☁️';
  };

  const getStateColor = (state) => {
    if (state === 'running' || state === 'active' || state === 'available' || state === 'attached') return '#39d353';
    if (state === 'terminated' || state === 'deleted' || state === 'deleting') return '#f85149';
    if (state === 'creating' || state === 'pending') return '#58a6ff';
    return '#8b949e';
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const groupByParent = () => {
    const parentMap = {};
    const childMap = {};
    
    // First pass: identify all parents and children
    resources.forEach(resource => {
      if (!resource.parent_resource_id) {
        parentMap[resource.resource_id] = { ...resource, children: [] };
      } else {
        if (!childMap[resource.parent_resource_id]) {
          childMap[resource.parent_resource_id] = [];
        }
        childMap[resource.parent_resource_id].push(resource);
      }
    });
    
    // Second pass: attach children to parents
    Object.keys(childMap).forEach(parentId => {
      if (parentMap[parentId]) {
        parentMap[parentId].children = childMap[parentId];
      } else {
        // Parent doesn't exist as a resource, create orphaned group
        childMap[parentId].forEach(child => {
          parentMap[child.resource_id] = { ...child, children: [] };
        });
      }
    });
    
    return Object.values(parentMap);
  };

  const filteredResources = () => {
    const grouped = groupByParent();
    if (filter === 'all') return grouped;
    
    const activeStates = ['running', 'active', 'available', 'attached', 'creating', 'pending'];
    const terminatedStates = ['terminated', 'deleted', 'deleting'];
    
    if (filter === 'active') {
      return grouped.map(r => ({
        ...r,
        children: r.children.filter(c => activeStates.includes(c.state))
      })).filter(r => activeStates.includes(r.state) || r.children.length > 0);
    }
    
    if (filter === 'terminated') {
      return grouped.map(r => ({
        ...r,
        children: r.children.filter(c => terminatedStates.includes(c.state))
      })).filter(r => terminatedStates.includes(r.state) || r.children.length > 0);
    }
    
    return grouped;
  };

  if (loading) return <div className="resources-loading">Loading resources...</div>;

  return (
    <div className="resources-container">
      <div className="resources-header">
        <h2>💾 Resource Inventory</h2>
        <div className="resources-filter">
          <button className={filter === 'all' ? 'active' : ''} onClick={() => setFilter('all')}>
            All ({resources.length})
          </button>
          <button className={filter === 'active' ? 'active' : ''} onClick={() => setFilter('active')}>
            Active
          </button>
          <button className={filter === 'terminated' ? 'active' : ''} onClick={() => setFilter('terminated')}>
            Terminated
          </button>
        </div>
      </div>

      <div className="resources-grid">
        {filteredResources().map((resource) => (
          <div key={resource.resource_id} className="resource-card">
            <div className="resource-main">
              <div className="resource-icon">{getResourceIcon(resource.resource_type)}</div>
              <div className="resource-info">
                <div className="resource-type">{resource.resource_type.replace(/_/g, ' ')}</div>
                <div className="resource-id">{resource.resource_id}</div>
                <div className="resource-timestamp">
                  🕐 {formatTimestamp(resource.last_updated)}
                </div>
                {resource.metadata && (
                  <div className="resource-runtime" style={{color: '#58a6ff', fontSize: '0.85em'}}>
                    ⏱️ {resource.metadata}
                  </div>
                )}
              </div>
              <div className="resource-state" style={{ color: getStateColor(resource.state) }}>
                ● {resource.state}
              </div>
            </div>

            {resource.children && resource.children.length > 0 && (
              <div className="resource-children">
                <div className="children-label">↳ Child Resources ({resource.children.length})</div>
                <div className="children-tree">
                  {resource.children.map((child) => (
                    <div key={child.resource_id} className="resource-child">
                      <div className="child-connector"></div>
                      <span className="child-icon">{getResourceIcon(child.resource_type)}</span>
                      <div className="child-info">
                        <div className="child-type">{child.resource_type.replace(/_/g, ' ')}</div>
                        <div className="child-id">{child.resource_id}</div>
                        <div className="child-timestamp">🕐 {formatTimestamp(child.last_updated)}</div>
                        {child.metadata && (
                          <div className="child-runtime" style={{color: '#58a6ff', fontSize: '0.8em'}}>
                            ⏱️ {child.metadata}
                          </div>
                        )}
                      </div>
                      <span className="child-state" style={{ color: getStateColor(child.state) }}>
                        ● {child.state}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default Resources;
