'use client';

import { motion } from 'framer-motion';
import { MapPin, Wifi, Calendar } from 'lucide-react';

interface Event {
  id: string;
  user_identifier: string;
  ip_address: string;
  country: string;
  city: string;
  risk_score: number;
  risk_level: string;
  threats_detected: string[];
  timestamp: string;
}

export default function EventsList({ token, events }: { token: string; events: Event[] }) {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return 'border-red-500 bg-red-500/10';
      case 'high': return 'border-orange-500 bg-orange-500/10';
      case 'medium': return 'border-blue-500 bg-blue-500/10';
      default: return 'border-green-500 bg-green-500/10';
    }
  };

  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-500 text-white';
      case 'high': return 'bg-orange-500 text-white';
      case 'medium': return 'bg-blue-500 text-white';
      default: return 'bg-green-500 text-white';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.6 }}
      className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20"
    >
      <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <span>📋</span>
        Recent Login Events
      </h2>

      <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
        {events.map((event, i) => (
          <motion.div
            key={event.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 + i * 0.1 }}
            className={`${getRiskColor(event.risk_level)} border-l-4 rounded-lg p-4`}
          >
            <div className="flex justify-between items-start mb-2">
              <div className="font-semibold text-white text-sm">
                {event.user_identifier}
              </div>
              <div className={`${getRiskBadgeColor(event.risk_level)} px-3 py-1 rounded-full text-xs font-bold`}>
                {event.risk_level.toUpperCase()} ({event.risk_score})
              </div>
            </div>

            <div className="flex gap-4 text-xs text-purple-200 mb-2">
              <div className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {event.city}, {event.country}
              </div>
              <div className="flex items-center gap-1">
                <Wifi className="w-3 h-3" />
                {event.ip_address}
              </div>
            </div>

            {event.threats_detected.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {event.threats_detected.map((threat, j) => (
                  <span
                    key={j}
                    className="bg-red-500/20 text-red-300 px-2 py-0.5 rounded-full text-xs"
                  >
                    ⚠️ {threat}
                  </span>
                ))}
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
