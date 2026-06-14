import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import client from '../api/client';

export default function Group() {
  const { id } = useParams();
  const [transactions, setTransactions] = useState([]);
  
  useEffect(() => {
    client.get(`/balances/group/${id}`).then(res => setTransactions(res.data)).catch(console.error);
  }, [id]);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Group Balances</h1>
      <div className="glass-panel p-8">
        <h2 className="text-2xl mb-6 font-semibold">Debt Simplification</h2>
        {transactions.length === 0 ? <p className="text-slate-400">No debts to settle. Everything is balanced!</p> : (
          <ul className="space-y-4">
            {transactions.map((t, i) => (
              <li key={i} className="flex justify-between items-center bg-slate-800/40 border border-slate-700 p-4 rounded-xl shadow-sm">
                <span className="text-slate-200">User <strong className="text-white">{t.from_user_id}</strong> owes User <strong className="text-white">{t.to_user_id}</strong></span>
                <span className="font-bold text-red-400 font-mono text-lg bg-red-400/10 px-3 py-1 rounded-lg">₹{t.amount}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
