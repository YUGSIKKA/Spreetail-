import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="p-8 max-w-7xl mx-auto animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
          Dashboard
        </h1>
        <button 
          onClick={handleLogout}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800/60 border border-slate-700 hover:bg-rose-500/10 hover:border-rose-500/30 text-slate-300 hover:text-rose-400 transition-all duration-300 transform active:scale-95 cursor-pointer"
        >
          <LogOut className="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/group/1" className="glass-card p-6 flex flex-col justify-between h-40 group">
          <h2 className="text-xl font-semibold transition-colors group-hover:text-indigo-300">Flatmates Group</h2>
          <span className="text-indigo-400 group-hover:translate-x-1 transition-transform inline-block">View Balances &rarr;</span>
        </Link>
        <Link to="/import" className="glass-card p-6 flex flex-col justify-between h-40 border-indigo-500/30 group">
          <h2 className="text-xl font-semibold transition-colors group-hover:text-indigo-300">Import CSV</h2>
          <span className="text-indigo-400 group-hover:translate-x-1 transition-transform inline-block">Upload & Analyze &rarr;</span>
        </Link>
      </div>
    </div>
  );
}
