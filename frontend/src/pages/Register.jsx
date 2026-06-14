import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import client from '../api/client';
import { UserPlus } from 'lucide-react';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      // 1. Register the user
      await client.post('/auth/register', {
        name,
        email,
        password,
      });

      // 2. Automatically log them in
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);
      
      const res = await client.post('/auth/login', params);
      localStorage.setItem('token', res.data.access_token);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-4 animate-fade-in">
      <div className="glass-panel w-full max-w-md p-8">
        <div className="flex justify-center mb-6">
          <div className="bg-indigo-500/20 p-4 rounded-full">
            <UserPlus className="w-10 h-10 text-indigo-400" />
          </div>
        </div>
        <h2 className="text-3xl font-bold text-center mb-6">Create Account</h2>
        
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 p-3 rounded-lg text-sm mb-6 text-center animate-shake">
            {error}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">Full Name</label>
            <input 
              type="text" 
              className="input-field" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Aisha Patel"
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">Email Address</label>
            <input 
              type="email" 
              className="input-field" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="aisha@example.com"
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">Password</label>
            <input 
              type="password" 
              className="input-field" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">Confirm Password</label>
            <input 
              type="password" 
              className="input-field" 
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              required 
            />
          </div>
          
          <button 
            type="submit" 
            className="btn-primary w-full text-lg py-2.5 transition-all duration-300 transform active:scale-95 flex items-center justify-center"
            disabled={loading}
          >
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-slate-400 text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold transition-colors duration-200">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
