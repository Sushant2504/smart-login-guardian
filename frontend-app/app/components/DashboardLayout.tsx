'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, Activity, AlertTriangle, TrendingUp, LogOut, RefreshCw } from 'lucide-react';
import ThreeDGlobe from './ThreeDGlobe';
import StatsCard from './StatsCard';
import EventsList from './EventsList';
import AlertsList from './AlertsList';
import CreateEvent from './CreateEvent';

const API_URL = 'http://localhost:8000/api/v1';

interface DashboardProps {
  user: any;
  token: string;
  onLogout: () => void;
}

export default function DashboardLayout({ user, token, onLogout }: DashboardProps) {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadDashboard = async () => {
    try {
      const response = await fetch(`${API_URL}/reports/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setDashboardData(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading Dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 mb-6 border border-white/20"
      >
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="bg-gradient-to-br from-purple-500 to-indigo-600 p-3 rounded-xl">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Smart Login Guardian</h1>
              <p className="text-purple-200 text-sm">Security Operations Center</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={loadDashboard}
              className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition"
            >
              <RefreshCw className="w-5 h-5 text-white" />
            </button>
            <div className="text-right">
              <p className="text-white font-semibold">{user?.full_name}</p>
              <p className="text-purple-200 text-sm uppercase">{user?.role}</p>
            </div>
            <button
              onClick={onLogout}
              className="bg-red-500/20 hover:bg-red-500/30 text-red-300 px-4 py-2 rounded-lg flex items-center gap-2 transition"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </motion.header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatsCard
          icon={Activity}
          label="Total Events"
          value={dashboardData?.total_events || 0}
          change="+12%"
          trend="up"
          delay={0}
        />
        <StatsCard
          icon={AlertTriangle}
          label="Active Alerts"
          value={dashboardData?.active_threats || 0}
          change="+2"
          trend="up"
          delay={0.1}
        />
        <StatsCard
          icon={TrendingUp}
          label="High Risk Events"
          value={dashboardData?.high_risk_events || 0}
          change="+1"
          trend="up"
          delay={0.2}
        />
        <StatsCard
          icon={Shield}
          label="Success Rate"
          value={`${dashboardData?.success_rate?.toFixed(1) || 0}%`}
          change="-5%"
          trend="down"
          delay={0.3}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* 3D Globe */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
          className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 h-[500px]"
        >
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span>🌍</span>
            Global Threat Map
          </h2>
          <ThreeDGlobe threats={dashboardData?.top_threat_countries || []} />
        </motion.div>

        {/* Create Event */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
        >
          <CreateEvent token={token} onEventCreated={loadDashboard} />
        </motion.div>
      </div>

      {/* Events and Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EventsList token={token} events={dashboardData?.recent_events || []} />
        <AlertsList token={token} alerts={dashboardData?.recent_alerts || []} onUpdate={loadDashboard} />
      </div>
    </div>
  );
}
