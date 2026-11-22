'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Mail, Lock, User, LogIn, ArrowLeft } from 'lucide-react';

const API_URL = 'http://localhost:8000/api/v1';

interface SignupScreenProps {
  onSignup: (user: any, token: string) => void;
  onBackToLogin: () => void;
}

export default function SignupScreen({ onSignup, onBackToLogin }: SignupScreenProps) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    // Validate password strength
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      setLoading(false);
      return;
    }

    try {
      // Register user
      const registerResponse = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
          role: 'viewer' // Default role
        })
      });

      if (!registerResponse.ok) {
        const errorData = await registerResponse.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      // Auto-login after successful registration
      const loginResponse = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });

      if (!loginResponse.ok) throw new Error('Auto-login failed');

      const data = await loginResponse.json();
      setSuccess(true);

      // Delay to show success message
      setTimeout(() => {
        onSignup(data.user, data.access_token);
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
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
        {/* Back Button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onBackToLogin}
          className="absolute top-6 left-6 p-2 bg-white/10 hover:bg-white/20 rounded-lg transition"
        >
          <ArrowLeft className="w-5 h-5 text-white" />
        </motion.button>

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
          Create Account
        </h1>
        <p className="text-purple-200 text-center mb-8">
          Join Smart Login Guardian
        </p>

        {success ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-green-500/20 border border-green-500/50 rounded-xl p-6 text-center"
          >
            <div className="text-6xl mb-4">✓</div>
            <div className="text-white font-semibold text-lg mb-2">Account Created!</div>
            <div className="text-green-200 text-sm">Logging you in...</div>
          </motion.div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-white text-sm font-semibold mb-2">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-300" />
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-12 py-3 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
                  placeholder="Enter your full name"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-white text-sm font-semibold mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-300" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
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
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-12 py-3 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
                  placeholder="Create a password"
                  required
                />
              </div>
              <p className="text-purple-300 text-xs mt-1">Minimum 8 characters</p>
            </div>

            <div>
              <label className="block text-white text-sm font-semibold mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-300" />
                <input
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-12 py-3 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
                  placeholder="Confirm your password"
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
                  Creating Account...
                </>
              ) : (
                <>
                  <LogIn className="w-5 h-5" />
                  Create Account
                </>
              )}
            </motion.button>
          </form>
        )}

        <div className="mt-6 text-center">
          <p className="text-purple-200 text-sm">
            Already have an account?{' '}
            <button
              onClick={onBackToLogin}
              className="text-white font-semibold hover:underline"
            >
              Sign In
            </button>
          </p>
        </div>

        <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10">
          <p className="text-purple-200 text-xs text-center">
            By creating an account, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </motion.div>
    </div>
  );
}
