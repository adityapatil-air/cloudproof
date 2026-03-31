import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, useParams, Navigate } from 'react-router-dom';
import './index.css';
import App from './App';
import Register from './Register';
import Auth from './pages/Auth';
import Setup from './pages/Setup';

function UserRoute() {
  const { username } = useParams();
  return <App username={username} />;
}

/** Redirect / → /login if not logged in, else → /<username> */
function HomeRedirect() {
  const user = JSON.parse(localStorage.getItem('cloudproof_user') || 'null');
  const token = localStorage.getItem('cloudproof_token');
  if (token && user?.username) return <Navigate to={`/${user.username}`} replace />;
  return <Navigate to="/login" replace />;
}

/** Protect routes that need a JWT token */
function PrivateRoute({ children }) {
  const token = localStorage.getItem('cloudproof_token');
  return token ? children : <Navigate to="/login" replace />;
}

/** Already logged-in users shouldn't see the login page */
function PublicRoute({ children }) {
  const user  = JSON.parse(localStorage.getItem('cloudproof_user') || 'null');
  const token = localStorage.getItem('cloudproof_token');
  if (token && user?.username) return <Navigate to={`/${user.username}`} replace />;
  return children;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Home: smart redirect based on auth state */}
        <Route path="/" element={<HomeRedirect />} />

        {/* Auth: sign in / create account */}
        <Route path="/login"    element={<PublicRoute><Auth /></PublicRoute>} />

        {/* AWS onboarding wizard (requires login) */}
        <Route path="/setup"    element={<PrivateRoute><Setup /></PrivateRoute>} />

        {/* Legacy register page (kept for backward compat) */}
        <Route path="/register" element={<Register />} />

        {/* Public profile viewer */}
        <Route path="/:username" element={<UserRoute />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
