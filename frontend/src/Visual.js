import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Visual({ userId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState(90);

  useEffect(() => {
    fetchData();
  }, [userId, filter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:5000/api/users/${userId}/dashboard?days=${filter}`);
      setData(response.data);
    } catch (error) {
      console.error('Error fetching visual data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getServiceIcon = (service) => {
    const icons = {
      'EC2': '🖥️',
      'S3': '🪣',
      'IAM': '🔐',
      'VPC': '🌐',
      'LAMBDA': '⚡',
      'RDS': '🗄️',
      'CLOUDFORMATION': '📚',
      'EKS': '☸️',
    };
    return icons[service] || '☁️';
  };

  const getActionIcon = (action) => {
    if (action.includes('Create')) return '➕';
    if (action.includes('Delete') || action.includes('Terminate')) return '🗑️';
    if (action.includes('Update') || action.includes('Modify')) return '✏️';
    if (action.includes('Stop')) return '⏸️';
    if (action.includes('Start') || action.includes('Run')) return '▶️';
    return '⚙️';
  };

  if (loading) return <div className="visual-loading">Loading visual data...</div>;
  if (!data) return null;

  return (
    <div className="visual-container">
      <div className="visual-header">
        <h3>📊 Visual Activity Timeline</h3>
        <div className="filter-buttons">
          <button className={filter === 7 ? 'active' : ''} onClick={() => setFilter(7)}>7 Days</button>
          <button className={filter === 30 ? 'active' : ''} onClick={() => setFilter(30)}>30 Days</button>
          <button className={filter === 90 ? 'active' : ''} onClick={() => setFilter(90)}>90 Days</button>
        </div>
      </div>

      <div className="visual-timeline">
        {data.dashboard.map((day) => (
          <div key={day.date} className="visual-day">
            <div className="visual-day-header">
              <span className="visual-date">{day.date}</span>
              <span className="visual-summary">{day.total_actions} actions • {day.total_score} pts</span>
            </div>
            <div className="visual-services">
              {Object.entries(day.services).map(([service, details]) => (
                <div key={service} className="visual-service">
                  <div className="visual-service-header">
                    <span className="visual-service-icon">{getServiceIcon(service)}</span>
                    <span className="visual-service-name">{service}</span>
                    <span className="visual-service-count">{details.count}</span>
                  </div>
                  <div className="visual-actions">
                    {Object.entries(
                      details.actions.reduce((acc, action) => {
                        acc[action.action] = (acc[action.action] || 0) + 1;
                        return acc;
                      }, {})
                    ).map(([action, count]) => (
                      <div key={action} className="visual-action">
                        <span className="visual-action-icon">{getActionIcon(action)}</span>
                        <span className="visual-action-name">{action}</span>
                        <span className="visual-action-count">×{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Visual;
