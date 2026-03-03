import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, useParams, Navigate } from 'react-router-dom';
import './index.css';
import App from './App';

function UserRoute() {
  const { username } = useParams();
  return <App username={username} />;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/:username" element={<UserRoute />} />
        <Route path="/" element={<Navigate to="/aditya" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
