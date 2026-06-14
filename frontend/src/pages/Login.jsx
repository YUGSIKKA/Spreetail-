import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import client from '../api/client';
import { LogIn } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('pass123');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);
      
      const res = await client.post('/auth/login', params);
      localStorage.setItem('token', res.data.access_token);
      navigate('/');
    } catch (err) {
      alert('Login failed. Check credentials.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-4 animate-fade-in">
      <div className="glass-panel w-full max-w-md p-8">
        <div className="flex justify-center mb-8">
          <div className="bg-indigo-500/20 p-4 rounded-full">
            <LogIn className="w-10 h-10 text-indigo-400" />
          </div>
        </div>
        <h2 className="text-3xl font-bold text-center mb-8">Welcome Back</h2>
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Email</label>
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
            <label className="block text-sm font-medium text-slate-400 mb-2">Password</label>
            <input 
              type="password" 
              className="input-field" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required 
            />
          </div>
          <button type="submit" className="btn-primary w-full text-lg">
            Sign In
          </button>
        </form>
        <div className="mt-6 text-center">
          <p className="text-slate-400 text-sm">
            Don't have an account?{' '}
            <Link to="/register" className="text-indigo-400 hover:text-indigo-300 font-semibold transition-colors duration-200">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
