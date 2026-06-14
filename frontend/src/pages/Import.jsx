import React, { useState } from 'react';
import client from '../api/client';
import { Upload, AlertCircle, CheckCircle, Info, ArrowRight } from 'lucide-react';

export default function Import() {
  const [file, setFile] = useState(null);
  const [previews, setPreviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const groupId = 1;

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('group_id', groupId);
    
    try {
      const res = await client.post('/import/preview', formData);
      setPreviews(res.data.previews);
    } catch (err) {
      setError('Failed to process CSV');
    } finally {
      setLoading(false);
    }
  };

  const handleCommit = async () => {
    const hasRed = previews.some(p => p.status === 'red');
    if (hasRed) {
      alert("Please resolve all red flagged rows before committing.");
      return;
    }
    
    try {
      const res = await client.post('/import/commit', {
        group_id: groupId,
        previews: previews
      });
      alert(`Import committed! Session ID: ${res.data.session_id}`);
      setPreviews([]);
      setFile(null);
    } catch(err) {
      alert("Failed to commit");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto animate-fade-in">
      <h1 className="text-4xl font-bold mb-8">Import CSV</h1>
      
      {!previews.length ? (
        <div className="glass-panel p-12 text-center border-dashed border-2 border-slate-600">
          <Upload className="w-16 h-16 mx-auto mb-4 text-indigo-400" />
          <h3 className="text-xl font-medium mb-4">Upload Shared Expenses CSV</h3>
          <input 
            type="file" 
            accept=".csv" 
            onChange={(e) => setFile(e.target.files[0])}
            className="mb-4 block mx-auto text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
          <button 
            onClick={handleUpload} 
            disabled={!file || loading}
            className="btn-primary"
          >
            {loading ? 'Processing...' : 'Analyze CSV'}
          </button>
          {error && <p className="text-red-400 mt-4">{error}</p>}
        </div>
      ) : (
        <div className="space-y-6 animate-slide-up">
          <div className="flex justify-between items-center glass-card p-6">
            <div>
              <h2 className="text-2xl font-semibold">Import Preview</h2>
              <p className="text-slate-400">Review anomalies and finalize the import</p>
            </div>
            <button onClick={handleCommit} className="btn-primary flex items-center gap-2">
              Commit Import <ArrowRight className="w-4 h-4" />
            </button>
          </div>
          
          <div className="overflow-x-auto glass-panel p-1">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-800/50">
                  <th className="p-4 rounded-tl-xl">Row</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Description</th>
                  <th className="p-4">Amount</th>
                  <th className="p-4">Anomalies Detected</th>
                  <th className="p-4 rounded-tr-xl">Action Needed</th>
                </tr>
              </thead>
              <tbody>
                {previews.map((row, i) => (
                  <tr key={i} className={`border-t border-slate-700/50 ${
                    row.status === 'red' ? 'bg-red-500/10' :
                    row.status === 'yellow' ? 'bg-yellow-500/10' :
                    row.status === 'grey' ? 'bg-slate-500/10 opacity-50' :
                    'bg-green-500/5'
                  }`}>
                    <td className="p-4 text-slate-400">#{row.row_number}</td>
                    <td className="p-4">
                      {row.status === 'red' && <AlertCircle className="text-red-400 w-5 h-5" />}
                      {row.status === 'yellow' && <Info className="text-yellow-400 w-5 h-5" />}
                      {row.status === 'green' && <CheckCircle className="text-green-400 w-5 h-5" />}
                      {row.status === 'grey' && <span className="text-slate-400 font-medium">SKIPPED</span>}
                    </td>
                    <td className="p-4">{row.raw_row.description || 'N/A'}</td>
                    <td className="p-4">{row.raw_row.amount || '0'}</td>
                    <td className="p-4">
                      {row.anomalies.map((a, j) => (
                        <div key={j} className="text-sm mb-1 text-slate-300">
                          <span className="font-semibold text-white">{a.type}:</span> {a.detail}
                        </div>
                      ))}
                    </td>
                    <td className="p-4">
                      {row.status === 'red' && (
                        <button className="text-sm bg-red-500/20 text-red-300 px-3 py-1 rounded hover:bg-red-500/30">
                          Resolve
                        </button>
                      )}
                      {row.status === 'yellow' && (
                        <span className="text-sm text-yellow-300">Auto-fixed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
