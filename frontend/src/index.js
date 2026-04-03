import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, useParams, Navigate } from 'react-router-dom';
import './index.css';
import App          from './App';
import Auth         from './pages/Auth';
import AuthCallback from './pages/AuthCallback';
import Setup        from './pages/Setup';
import ResetPassword from './pages/ResetPassword';

function UserRoute() {
  const { username } = useParams();
  return <App username={username} />;
}

/** / → profile if logged in, else → /login */
function HomeRedirect() {
  const user  = JSON.parse(localStorage.getItem('cloudproof_user') || 'null');
  const token = localStorage.getItem('cloudproof_token');
  if (token && user?.username) return <Navigate to={`/${user.username}`} replace />;
  return <Navigate to="/login" replace />;
}

/** Redirects to /login if no JWT */
function PrivateRoute({ children }) {
  const token = localStorage.getItem('cloudproof_token');
  return token ? children : <Navigate to="/login" replace />;
}

/** Already signed-in users skip the login page */
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
        {/* Smart home redirect */}
        <Route path="/" element={<HomeRedirect />} />

        {/* Auth pages */}
        <Route path="/login"          element={<PublicRoute><Auth /></PublicRoute>} />
        <Route path="/auth/callback"  element={<AuthCallback />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* AWS onboarding (requires login) */}
        <Route path="/setup" element={<PrivateRoute><Setup /></PrivateRoute>} />

        {/* Legacy register (kept for backward compat) */}

        {/* Public profile viewer */}
        <Route path="/:username" element={<UserRoute />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
