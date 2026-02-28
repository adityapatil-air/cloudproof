import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import CalendarHeatmap from 'react-calendar-heatmap';
import 'react-calendar-heatmap/dist/styles.css';
import axios from 'axios';

function Profile() {
  const { username } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await axios.get(
          `http://localhost:5000/api/profile/${encodeURIComponent(username)}`
        );

        setData(response.data);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    };

    if (username) fetchProfile();
  }, [username]);

  // Convert backend heatmap { "2025-02-20": 14 } → array with Date at local midnight (matches library index calc)
  const heatmapArray = (() => {
    if (!data?.heatmap || typeof data.heatmap !== 'object') return [];
    return Object.entries(data.heatmap)
      .filter(([k]) => k && typeof k === 'string')
      .map(([dateStr, count]) => {
        const parts = String(dateStr).split(/[-/]/);
        if (parts.length < 3) return null;
        const y = parseInt(parts[0], 10);
        const m = parseInt(parts[1], 10) - 1;
        const d = parseInt(parts[2], 10);
        if (isNaN(y) || isNaN(m) || isNaN(d)) return null;
        const date = new Date(y, m, d);
        if (isNaN(date.getTime())) return null;
        return { date, count: Number(count) || 0 };
      })
      .filter(Boolean);
  })();

  // GitHub-style color scaling
  const getColorClass = (value) => {
    if (!value || value.count === 0) return 'color-empty';
    if (value.count < 5) return 'color-scale-1';
    if (value.count < 10) return 'color-scale-2';
    if (value.count < 20) return 'color-scale-3';
    return 'color-scale-4';
  };

  const now = new Date();
  const endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  if (loading) return <p style={{ textAlign: 'center' }}>Loading profile...</p>;
  if (error) return <p style={{ textAlign: 'center', color: 'red' }}>{error}</p>;

  return (
    <div className="profile-page">
      <div className="profile-container">
        <h1 className="profile-username">@{data?.username}</h1>

        <div className="profile-heatmap-section">
          <CalendarHeatmap
            numDays={730}
            endDate={endDate}
            values={heatmapArray}
            valueKey="count"
            classForValue={getColorClass}
            titleForValue={(v) => v ? `${v.date?.toLocaleDateString?.() ?? v.date}: ${v.count}` : null}
            showWeekdayLabels={true}
          />

          <div className="legend">
            <span>Less</span>
            <div className="legend-box color-empty"></div>
            <div className="legend-box color-scale-1"></div>
            <div className="legend-box color-scale-2"></div>
            <div className="legend-box color-scale-3"></div>
            <div className="legend-box color-scale-4"></div>
            <span>More</span>
          </div>
        </div>

        {data?.services && (
          <div className="profile-services">
            <h3>Service Breakdown</h3>
            <ul>
              {Object.entries(data.services).map(([service, score]) => (
                <li key={service}>
                  {service} — {score}
                </li>
              ))}
            </ul>
          </div>
        )}

        <h3>Total Score: {data?.total_score}</h3>
      </div>
    </div>
  );
}

export default Profile;