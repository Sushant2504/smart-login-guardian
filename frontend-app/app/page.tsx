'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import LoginScreen from './components/LoginScreen';
import SignupScreen from './components/SignupScreen';

// Dynamically import Three.js components (client-side only)
const DynamicDashboard = dynamic(() => import('./components/DashboardLayout'), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center h-screen bg-gradient-to-br from-purple-900 to-indigo-900">
    <div className="text-white text-2xl">Loading Dashboard...</div>
  </div>
});

type Screen = 'login' | 'signup' | 'dashboard';

export default function Home() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('login');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState<string | null>(null);

  const handleLogin = (userData: any, authToken: string) => {
    setUser(userData);
    setToken(authToken);
    setCurrentScreen('dashboard');
  };

  const handleSignup = (userData: any, authToken: string) => {
    setUser(userData);
    setToken(authToken);
    setCurrentScreen('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    setCurrentScreen('login');
  };

  const showSignup = () => setCurrentScreen('signup');
  const showLogin = () => setCurrentScreen('login');

  if (currentScreen === 'login') {
    return <LoginScreen onLogin={handleLogin} onShowSignup={showSignup} />;
  }

  if (currentScreen === 'signup') {
    return <SignupScreen onSignup={handleSignup} onBackToLogin={showLogin} />;
  }

  return <DynamicDashboard user={user} token={token} onLogout={handleLogout} />;
}
