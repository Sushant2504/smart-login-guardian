'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Rocket } from 'lucide-react';

const API_URL = 'http://localhost:8000/api/v1';

export default function CreateEvent({
  token,
  onEventCreated
}: {
  token: string;
  onEventCreated: () => void;
}) {
  const [formData, setFormData] = useState({
    user_identifier: 'test@company.com',
    ip_address: '185.220.101.99',
    country: 'Russia',
    city: 'Moscow',
    status: 'failed',
    user_agent: ''
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      setResult(data);
      onEventCreated();

      // Auto-clear result after 5 seconds
      setTimeout(() => setResult(null), 5000);
    } catch (error) {
      console.error('Failed to create event:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 h-full">
      <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <span>➕</span>
        Simulate Login Event
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="User Email"
            value={formData.user_identifier}
            onChange={(e) => setFormData({ ...formData, user_identifier: e.target.value })}
            className="bg-slate-900/50 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <input
            type="text"
            placeholder="IP Address"
            value={formData.ip_address}
            onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
            className="bg-slate-900/50 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Country"
            value={formData.country}
            onChange={(e) => setFormData({ ...formData, country: e.target.value })}
            className="bg-slate-900/50 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <input
            type="text"
            placeholder="City"
            value={formData.city}
            onChange={(e) => setFormData({ ...formData, city: e.target.value })}
            className="bg-slate-900/50 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <select
          value={formData.status}
          onChange={(e) => setFormData({ ...formData, status: e.target.value })}
          className="w-full bg-slate-900/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="blocked">Blocked</option>
        </select>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          type="submit"
          disabled={loading}
          className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-3 rounded-lg font-semibold flex items-center justify-center gap-2 hover:shadow-lg transition disabled:opacity-50"
        >
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Rocket className="w-5 h-5" />
              Create Event & Analyze
            </>
          )}
        </motion.button>
      </form>

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`mt-4 p-4 rounded-lg border-l-4 ${
            result.risk_level === 'critical' || result.risk_level === 'high'
              ? 'bg-red-500/20 border-red-500'
              : result.risk_level === 'medium'
              ? 'bg-orange-500/20 border-orange-500'
              : 'bg-green-500/20 border-green-500'
          }`}
        >
          <div className="text-white font-semibold mb-2">
            Event Created! Risk Score: {result.risk_score}/100
          </div>
          <div className="text-sm text-purple-200">
            Risk Level: <span className="font-bold uppercase">{result.risk_level}</span>
          </div>
          {result.is_suspicious && (
            <div className="mt-2 text-xs text-red-300">
              ⚠️ High-risk event detected - Alert automatically generated!
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
