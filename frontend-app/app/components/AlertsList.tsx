'use client';

import { motion } from 'framer-motion';
import { Check, X } from 'lucide-react';

const API_URL = 'http://localhost:8000/api/v1';

interface Alert {
  id: string;
  title: string;
  description: string;
  status: string;
  severity: string;
  created_at: string;
}

export default function AlertsList({
  token,
  alerts,
  onUpdate
}: {
  token: string;
  alerts: Alert[];
  onUpdate: () => void;
}) {
  const handleAcknowledge = async (alertId: string) => {
    try {
      await fetch(`${API_URL}/alerts/${alertId}/acknowledge`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      onUpdate();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const handleResolve = async (alertId: string) => {
    try {
      await fetch(`${API_URL}/alerts/${alertId}/resolve`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      onUpdate();
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'border-red-500 bg-red-500/10';
      case 'acknowledged': return 'border-orange-500 bg-orange-500/10';
      default: return 'border-green-500 bg-green-500/10';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open': return 'bg-red-500 text-white';
      case 'acknowledged': return 'bg-orange-500 text-white';
      default: return 'bg-green-500 text-white';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.7 }}
      className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20"
    >
      <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <span>🚨</span>
        Security Alerts
      </h2>

      <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
        {alerts.map((alert, i) => (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.8 + i * 0.1 }}
            className={`${getStatusColor(alert.status)} border-l-4 rounded-lg p-4`}
          >
            <div className="flex justify-between items-start mb-2">
              <div className="font-semibold text-white text-sm">
                {alert.title}
              </div>
              <div className={`${getStatusBadge(alert.status)} px-3 py-1 rounded-full text-xs font-bold uppercase`}>
                {alert.status}
              </div>
            </div>

            <p className="text-purple-200 text-xs mb-3">
              {alert.description}
            </p>

            {alert.status === 'open' && (
              <div className="flex gap-2">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleAcknowledge(alert.id)}
                  className="flex-1 bg-orange-500/20 hover:bg-orange-500/30 text-orange-300 px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1 transition"
                >
                  <Check className="w-3 h-3" />
                  Acknowledge
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleResolve(alert.id)}
                  className="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-300 px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1 transition"
                >
                  <Check className="w-3 h-3" />
                  Resolve
                </motion.button>
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
