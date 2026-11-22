'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Mail, Lock, LogIn } from 'lucide-react';

const API_URL = 'http://localhost:8000/api/v1';

interface LoginScreenProps {
  onLogin: (user: any, token: string) => void;
  onShowSignup: () => void;
}

export default function LoginScreen({ onLogin, onShowSignup }: LoginScreenProps) {
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('Admin123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) throw new Error('Login failed');

      const data = await response.json();
      onLogin(data.user, data.access_token);
    } catch (err) {
      setError('Invalid credentials. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 flex items-center justify-center p-4">
      {/* Animated background particles */}
      <div className="absolute inset-0 overflow-hidden">
        {typeof window !== 'undefined' && [...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-white rounded-full"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
              opacity: Math.random() * 0.5
            }}
            animate={{
              y: [null, Math.random() * window.innerHeight],
              opacity: [null, Math.random() * 0.5]
            }}
            transition={{
              duration: Math.random() * 10 + 10,
              repeat: Infinity,
              ease: 'linear'
            }}
          />
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-white/10 backdrop-blur-xl p-10 rounded-3xl shadow-2xl w-full max-w-md border border-white/20 relative z-10"
      >
        {/* Logo */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring' }}
          className="flex justify-center mb-6"
        >
          <div className="bg-gradient-to-br from-purple-500 to-indigo-600 p-4 rounded-2xl">
            <Shield className="w-12 h-12 text-white" />
          </div>
        </motion.div>

        <h1 className="text-3xl font-bold text-white text-center mb-2">
          Smart Login Guardian
        </h1>
        <p className="text-purple-200 text-center mb-8">
          Enterprise Identity Threat Detection
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-300" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-xl px-12 py-3 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
                placeholder="Enter your email"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-300" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-xl px-12 py-3 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
                placeholder="Enter your password"
                required
              />
            </div>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-500/20 border border-red-500/50 rounded-xl p-3 text-red-200 text-sm"
            >
              {error}
            </motion.div>
          )}

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2 hover:shadow-lg transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Signing In...
              </>
            ) : (
              <>
                <LogIn className="w-5 h-5" />
                Sign In to Dashboard
              </>
            )}
          </motion.button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-purple-200 text-sm">
            Don't have an account?{' '}
            <button
              onClick={onShowSignup}
              className="text-white font-semibold hover:underline"
            >
              Sign Up
            </button>
          </p>
        </div>

        <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10">
          <p className="text-purple-200 text-sm text-center">
            <span className="font-semibold">Demo Credentials:</span>
          </p>
          <p className="text-white text-sm text-center mt-1">
            admin@example.com / Admin123!
          </p>
        </div>
      </motion.div>
    </div>
  );
}
