import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, useParams, Navigate } from 'react-router-dom';
import './index.css';
import App from './App';
import Register from './Register';

function UserRoute() {
  const { username } = useParams();
  return <App username={username} />;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/demo1" replace />} />
        <Route path="/register" element={<Register />} />
        <Route path="/:username" element={<UserRoute />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
