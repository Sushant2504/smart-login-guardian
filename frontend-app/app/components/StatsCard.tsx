'use client';

import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  change: string;
  trend: 'up' | 'down';
  delay: number;
}

export default function StatsCard({ icon: Icon, label, value, change, trend, delay }: StatsCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ scale: 1.05 }}
      className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 relative overflow-hidden group"
    >
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      <div className="relative z-10">
        <div className="flex justify-between items-start mb-4">
          <div className="bg-gradient-to-br from-purple-500 to-indigo-600 p-3 rounded-xl">
            <Icon className="w-6 h-6 text-white" />
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
            trend === 'up'
              ? 'bg-red-500/20 text-red-300'
              : 'bg-green-500/20 text-green-300'
          }`}>
            {change}
          </div>
        </div>

        <div className="text-3xl font-bold text-white mb-1">
          {value}
        </div>
        <div className="text-purple-200 text-sm">
          {label}
        </div>
      </div>

      {/* Particle effect on hover */}
      <motion.div
        className="absolute -bottom-4 -right-4 w-32 h-32 bg-purple-500 rounded-full blur-3xl opacity-0 group-hover:opacity-30 transition-opacity duration-500"
      />
    </motion.div>
  );
}
