import React, { useState, useEffect } from 'react';
import CalendarHeatmap from 'react-calendar-heatmap';
import 'react-calendar-heatmap/dist/styles.css';
import axios from 'axios';

function App() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const userId = 1;

  useEffect(() => {
    fetchUserActivity();
  }, []);

  const fetchUserActivity = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`http://localhost:5000/api/users/${userId}/activity`);
      setUserData(response.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError(error.response?.data?.error || 'Failed to load activity data');
    } finally {
      setLoading(false);
    }
  };

  const getHeatmapData = () => {
    if (!userData || !userData.heatmap) return [];
    
    return Object.entries(userData.heatmap).map(([date, score]) => ({
      date: date,
      count: score
    }));
  };

  const getColorClass = (value) => {
    if (!value || value.count === 0) return 'color-empty';
    if (value.count < 5) return 'color-scale-1';
    if (value.count < 10) return 'color-scale-2';
    if (value.count < 20) return 'color-scale-3';
    return 'color-scale-4';
  };

  if (loading) {
    return (
      <div className="container">
        <div className="header">
          <h1>☁️ CloudProof</h1>
          <p>Loading your AWS activity...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="header">
          <h1>☁️ CloudProof</h1>
          <p style={{color: '#f85149'}}>Error: {error}</p>
          <button onClick={fetchUserActivity} style={{
            marginTop: '20px',
            padding: '10px 20px',
            background: '#238636',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}>Retry</button>
        </div>
      </div>
    );
  }

  const endDate = new Date();
  const startDate = new Date();
  startDate.setFullYear(startDate.getFullYear() - 1);

  return (
    <div className="container">
      <div className="header">
        <h1>☁️ CloudProof</h1>
        <p>Verified AWS Hands-On Activity Tracker</p>
      </div>

      <div className="profile-card">
        <div className="profile-header">
          <div className="profile-info">
            <h2>DevOps Engineer</h2>
            <p>AWS Cloud Practitioner</p>
          </div>
          <div className="stats">
            <div className="stat-item">
              <div className="stat-value">{userData?.total_score || 0}</div>
              <div className="stat-label">Total Score</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{Object.keys(userData?.services || {}).length}</div>
              <div className="stat-label">Services Used</div>
            </div>
          </div>
        </div>
      </div>

      <div className="activity-section">
        <h3 className="section-title">📊 Activity Contribution Graph</h3>
        <div className="heatmap-container">
          {getHeatmapData().length > 0 ? (
            <>
              <CalendarHeatmap
                startDate={startDate}
                endDate={endDate}
                values={getHeatmapData()}
                classForValue={getColorClass}
                showWeekdayLabels={true}
              />
              <div className="legend">
                <span>Less</span>
                <div className="legend-item">
                  <div className="legend-box" style={{background: '#161b22'}}></div>
                </div>
                <div className="legend-item">
                  <div className="legend-box" style={{background: '#0e4429'}}></div>
                </div>
                <div className="legend-item">
                  <div className="legend-box" style={{background: '#006d32'}}></div>
                </div>
                <div className="legend-item">
                  <div className="legend-box" style={{background: '#26a641'}}></div>
                </div>
                <div className="legend-item">
                  <div className="legend-box" style={{background: '#39d353'}}></div>
                </div>
                <span>More</span>
              </div>
            </>
          ) : (
            <p style={{textAlign: 'center', padding: '40px', color: '#8b949e'}}>
              No activity data available yet. Start using AWS services to see your contribution graph!
            </p>
          )}
        </div>
      </div>

      {Object.keys(userData?.services || {}).length > 0 && (
        <div className="activity-section">
          <h3 className="section-title">🔧 Service Breakdown</h3>
          <div className="services-grid">
            {Object.entries(userData.services).map(([service, score]) => (
              <div key={service} className="service-card">
                <div className="service-name">{service}</div>
                <div className="service-score">{score}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {userData?.recent_actions?.length > 0 && (
        <div className="activity-section">
          <h3 className="section-title">⚡ Recent Activity</h3>
          <div className="recent-activity">
            <ul className="activity-list">
              {userData.recent_actions.slice(0, 10).map((action, index) => (
                <li key={index} className="activity-item">
                  <div className="activity-details">
                    <span className="activity-service">{action.service}</span>
                    <span className="activity-action">{action.action}</span>
                  </div>
                  <span className="activity-score">+{action.score}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
