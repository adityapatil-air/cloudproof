import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Dashboard({ userId }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(90);

  useEffect(() => {
    fetchDashboard();
  }, [userId, days]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:5000/api/users/${userId}/dashboard?days=${days}`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) return <div className="dashboard-loading">Loading dashboard...</div>;
  if (!dashboardData) return null;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>📊 Daily Usage Dashboard</h2>
        <div className="days-filter">
          <button className={days === 7 ? 'active' : ''} onClick={() => setDays(7)}>7 Days</button>
          <button className={days === 30 ? 'active' : ''} onClick={() => setDays(30)}>30 Days</button>
          <button className={days === 90 ? 'active' : ''} onClick={() => setDays(90)}>90 Days</button>
        </div>
      </div>

      <div className="daily-cards">
        {dashboardData.dashboard.map((day) => (
          <div key={day.date} className="day-card">
            <div className="day-header">
              <h3>{new Date(day.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</h3>
              <div className="day-summary">
                <span>{day.total_actions} actions</span>
                <span>•</span>
                <span>{day.total_score} points</span>
              </div>
            </div>

            <div className="services-timeline">
              {Object.entries(day.services).map(([service, data]) => (
                <div key={service} className="service-section">
                  <div className="service-header">
                    <span className="service-badge">{service}</span>
                    <span className="service-count">{data.count} actions • {data.total_score} pts</span>
                  </div>
                  
                  <div className="actions-list">
                    {data.actions.map((action, idx) => (
                      <div key={idx} className="action-item">
                        <span className="action-time">{formatTime(action.timestamp)}</span>
                        <span className="action-name">{action.action}</span>
                        <span className="action-score">+{action.score}</span>
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

export default Dashboard;
