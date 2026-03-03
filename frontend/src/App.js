import React, { useState, useEffect } from 'react';
import CalendarHeatmap from 'react-calendar-heatmap';
import 'react-calendar-heatmap/dist/styles.css';
import axios from 'axios';
import Dashboard from './Dashboard';
import Visual from './Visual';
import Resources from './Resources';

function App({ username }) {
  const [userData, setUserData] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [view, setView] = useState('heatmap');

  const fetchUserActivity = async (userId) => {
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

  const fetchUser = async () => {
    try {
      const usersResponse = await axios.get('http://localhost:5000/api/users');
      const foundUser = usersResponse.data.find(u => u.email.split('@')[0] === username);
      if (!foundUser) {
        setError('User not found');
        setLoading(false);
        return;
      }
      setUser(foundUser);
      fetchUserActivity(foundUser.id);
    } catch (error) {
      setError('Failed to load user');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [username]);

  const getAvailableYears = () => {
    if (!userData || !userData.heatmap) return [new Date().getFullYear()];
    const years = Object.keys(userData.heatmap).map(date => new Date(date).getFullYear());
    return [...new Set(years)].sort((a, b) => b - a);
  };

  const getHeatmapData = () => {
    if (!userData || !userData.heatmap) return [];
    
    return Object.entries(userData.heatmap)
      .filter(([date]) => new Date(date).getFullYear() === selectedYear)
      .map(([date, score]) => ({
        date: date,
        count: score
      }));
  };

  const calculateStreaks = () => {
    if (!userData || !userData.heatmap) return { current: 0, max: 0 };
    
    const allDates = Object.keys(userData.heatmap)
      .map(date => new Date(date))
      .sort((a, b) => a - b);
    
    if (allDates.length === 0) return { current: 0, max: 0 };
    
    let maxStreak = 1;
    let tempStreak = 1;
    
    for (let i = 1; i < allDates.length; i++) {
      const diffDays = (allDates[i] - allDates[i-1]) / (1000 * 60 * 60 * 24);
      if (diffDays === 1) {
        tempStreak++;
        maxStreak = Math.max(maxStreak, tempStreak);
      } else {
        tempStreak = 1;
      }
    }
    
    let currentStreak = 1;
    for (let i = allDates.length - 2; i >= 0; i--) {
      const diffDays = (allDates[i + 1] - allDates[i]) / (1000 * 60 * 60 * 24);
      if (diffDays === 1) {
        currentStreak++;
      } else {
        break;
      }
    }
    
    return { current: currentStreak, max: maxStreak };
  };

  const getYearStats = () => {
    const yearData = getHeatmapData();
    const totalDays = yearData.length;
    const totalScore = yearData.reduce((sum, day) => sum + day.count, 0);
    return { totalDays, totalScore };
  };

  const streaks = calculateStreaks();

  const getColorClass = (value) => {
    if (!value || value.count === 0) return 'color-empty';
    if (value.count < 10) return 'color-scale-1';
    if (value.count < 25) return 'color-scale-2';
    if (value.count < 50) return 'color-scale-3';
    return 'color-scale-4';
  };

  const handleDayClick = (value) => {
    if (value && value.count > 0) {
      setSelectedDay(value);
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="header">
          <h1>☁️ CloudProof</h1>
          <p className="loading-text">Loading your AWS activity...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="header">
          <h1>☁️ CloudProof</h1>
          <p className="error-text">Error: {error}</p>
          <button onClick={fetchUser} className="retry-btn">Retry</button>
        </div>
      </div>
    );
  }

  const endDate = new Date(selectedYear, 11, 31);
  const startDate = new Date(selectedYear, 0, 1);
  const availableYears = getAvailableYears();
  const yearStats = getYearStats();

  return (
    <div className="container">
      <div className="header">
        <h1>☁️ CloudProof</h1>
        <p>Verified AWS Hands-On Activity Tracker</p>
        <div className="view-toggle">
          <button 
            className={view === 'heatmap' ? 'active' : ''}
            onClick={() => setView('heatmap')}
          >
            📊 Heatmap
          </button>
          <button 
            className={view === 'dashboard' ? 'active' : ''}
            onClick={() => setView('dashboard')}
          >
            📋 Dashboard
          </button>
          <button 
            className={view === 'visual' ? 'active' : ''}
            onClick={() => setView('visual')}
          >
            🎨 Visual
          </button>
          <button 
            className={view === 'resources' ? 'active' : ''}
            onClick={() => setView('resources')}
          >
            💾 Resources
          </button>
        </div>
      </div>

      {view === 'dashboard' ? (
        <Dashboard userId={user?.id} />
      ) : view === 'visual' ? (
        <Visual userId={user?.id} />
      ) : view === 'resources' ? (
        <Resources userId={user?.id} />
      ) : (
        <>
          <div className="profile-card">
            <div className="profile-header">
              <div className="profile-info">
                <h2>{user?.name || 'User'}</h2>
                <p>{user?.email || ''}</p>
              </div>
              <div className="stats">
                <div className="stat-item">
                  <div className="stat-value">{userData?.total_score || 0}</div>
                  <div className="stat-label">Total Score</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">
                    {streaks.current > 0 ? `🔥 ${streaks.current}` : streaks.current}
                  </div>
                  <div className="stat-label">Current Streak</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{Object.keys(userData?.services || {}).length}</div>
                  <div className="stat-label">Services Used</div>
                </div>
              </div>
            </div>
          </div>

          <div className="activity-section">
            <div className="heatmap-header">
              <h3 className="section-title">📊 Activity Contribution Graph - {selectedYear}</h3>
              <div className="year-selector">
                {availableYears.map(year => (
                  <button
                    key={year}
                    className={`year-btn ${selectedYear === year ? 'active' : ''}`}
                    onClick={() => setSelectedYear(year)}
                  >
                    {year}
                  </button>
                ))}
              </div>
            </div>

            <div className="year-stats">
              <div className="year-stat-item">
                <span className="year-stat-value">{yearStats.totalScore}</span>
                <span className="year-stat-label">points in {selectedYear}</span>
              </div>
              <div className="year-stat-item">
                <span className="year-stat-value">{yearStats.totalDays}</span>
                <span className="year-stat-label">active days</span>
              </div>
              <div className="year-stat-item">
                <span className="year-stat-value">
                  {streaks.current > 0 ? `🔥 ${streaks.current}` : streaks.current}
                </span>
                <span className="year-stat-label">current streak</span>
              </div>
              <div className="year-stat-item">
                <span className="year-stat-value">{streaks.max}</span>
                <span className="year-stat-label">longest streak</span>
              </div>
            </div>

            <div className="heatmap-container">
              {getHeatmapData().length > 0 ? (
                <>
                  <CalendarHeatmap
                    startDate={startDate}
                    endDate={endDate}
                    values={getHeatmapData()}
                    classForValue={getColorClass}
                    showWeekdayLabels={true}
                    onClick={handleDayClick}
                    titleForValue={(value) => {
                      if (!value || !value.date) return '';
                      return `${value.date}: ${value.count || 0} points`;
                    }}
                  />
                  <div className="legend">
                    <span>Less</span>
                    <div className="legend-box" style={{background: '#161b22'}}></div>
                    <div className="legend-box" style={{background: '#0e4429'}}></div>
                    <div className="legend-box" style={{background: '#006d32'}}></div>
                    <div className="legend-box" style={{background: '#26a641'}}></div>
                    <div className="legend-box" style={{background: '#39d353'}}></div>
                    <span>More</span>
                  </div>
                </>
              ) : (
                <p className="no-data">No activity in {selectedYear}. Select another year or start using AWS services!</p>
              )}
            </div>
          </div>

          {selectedDay && (
            <div className="selected-day-card">
              <div className="selected-day-header">
                <h3>📅 {selectedDay.date}</h3>
                <button onClick={() => setSelectedDay(null)} className="close-btn">✕</button>
              </div>
              <div className="selected-day-score">
                <span className="score-label">Total Score:</span>
                <span className="score-value">{selectedDay.count} points</span>
              </div>
            </div>
          )}

          {Object.keys(userData?.services || {}).length > 0 && (
            <div className="activity-section">
              <h3 className="section-title">🔧 Service Breakdown</h3>
              <div className="services-grid">
                {Object.entries(userData.services)
                  .sort(([, a], [, b]) => b - a)
                  .map(([service, score]) => (
                    <div key={service} className="service-card">
                      <div className="service-icon">{getServiceIcon(service)}</div>
                      <div className="service-name">{service}</div>
                      <div className="service-score">{score}</div>
                      <div className="service-bar">
                        <div 
                          className="service-bar-fill" 
                          style={{width: `${(score / Math.max(...Object.values(userData.services))) * 100}%`}}
                        ></div>
                      </div>
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
                        <span className="activity-date">{action.date}</span>
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
        </>
      )}
    </div>
  );
}

function getServiceIcon(service) {
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
}

export default App;
