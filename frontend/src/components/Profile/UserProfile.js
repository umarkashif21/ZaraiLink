import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { motion } from 'framer-motion';
import Navbar from '../Layout/Navbar';
import api from '../../services/api';

const API_BASE = process.env.REACT_APP_API_BASE_URL;

const UserProfile = () => {
  const { user, tokenBalance, refreshUser } = useAuth();
  const navigate = useNavigate();

  const [entitlements, setEntitlements] = useState([]);
  const [tokenHistory, setTokenHistory] = useState([]);
  const [telemetry, setTelemetry] = useState({ tokensSpent: 0, topCategory: 'None' });
  const [loading, setLoading] = useState(true);

  const [editingName, setEditingName] = useState(false);
  const [nameValue, setNameValue] = useState('');
  const [nameLoading, setNameLoading] = useState(false);
  const [nameMsg, setNameMsg] = useState(null);

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [pwLoading, setPwLoading] = useState(false);
  const [pwMsg, setPwMsg] = useState(null);

  useEffect(() => {
    const fetchProfileData = async () => {
      try {
        const response = await api.get('/subscriptions/profile-data/');
        setEntitlements(response.data.entitlements || []);
        setTokenHistory(response.data.tokenHistory || []);
        if (response.data.telemetry) {
          setTelemetry({
            tokensSpent: response.data.telemetry.tokensSpent || 0,
            topCategory: response.data.telemetry.topCategory || 'None',
          });
        }
      } catch (err) {
        console.error('Failed to load profile data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfileData();
  }, []);

  useEffect(() => {
    if (user?.name) setNameValue(user.name);
  }, [user]);

  const handleSaveName = async () => {
    if (!nameValue.trim()) return;
    setNameLoading(true);
    setNameMsg(null);
    try {
      const res = await fetch(`${API_BASE}/accounts/api/update-profile/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name: nameValue.trim() }),
      });
      const data = await res.json();
      if (data.success) {
        setNameMsg({ type: 'success', text: 'Name updated!' });
        setEditingName(false);
        if (refreshUser) refreshUser();
      } else {
        setNameMsg({ type: 'error', text: data.error || 'Failed to update name.' });
      }
    } catch {
      setNameMsg({ type: 'error', text: 'Network error. Try again.' });
    } finally {
      setNameLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwMsg(null);
    if (newPw !== confirmPw) {
      setPwMsg({ type: 'error', text: 'New passwords do not match.' });
      return;
    }
    if (newPw.length < 8) {
      setPwMsg({ type: 'error', text: 'Password must be at least 8 characters.' });
      return;
    }
    setPwLoading(true);
    try {
      const res = await fetch(`${API_BASE}/accounts/api/change-password/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ current_password: currentPw, new_password: newPw }),
      });
      const data = await res.json();
      if (data.success) {
        setPwMsg({ type: 'success', text: 'Password changed successfully!' });
        setCurrentPw(''); setNewPw(''); setConfirmPw('');
        setTimeout(() => setShowPasswordForm(false), 1500);
      } else {
        setPwMsg({ type: 'error', text: data.error || 'Failed to change password.' });
      }
    } catch {
      setPwMsg({ type: 'error', text: 'Network error. Try again.' });
    } finally {
      setPwLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 font-sans flex items-center justify-center">
        <div className="text-emerald-400 font-bold animate-pulse">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 font-sans selection:bg-emerald-500/30 selection:text-emerald-200">
      <Navbar />
      <div className="text-slate-300 py-12 px-6 lg:px-12">
        <div className="max-w-[1400px] mx-auto space-y-8">

          <header className="mb-10">
            <h1 className="text-4xl font-black text-white tracking-tight">My Profile</h1>
            <p className="text-slate-500 mt-2 text-lg">Manage your account, token wallet, and data access.</p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

            <div className="space-y-8 lg:col-span-1">

              <motion.section
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden"
              >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500" />
                <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                  <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Account
                </h2>

                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-500 to-blue-500 flex items-center justify-center text-white font-bold text-2xl shadow-inner flex-shrink-0">
                    {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                  </div>
                  <div className="min-w-0">
                    <div className="text-lg font-bold text-white truncate">{user?.name || 'ZaraiLink User'}</div>
                    <div className="text-sm text-slate-500 truncate">{user?.email}</div>
                    <div className="mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5" />
                      Active
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-800/50 space-y-3">
                  {!editingName ? (
                    <button
                      onClick={() => { setEditingName(true); setNameMsg(null); }}
                      className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors border border-slate-700 hover:border-slate-600 flex justify-between items-center"
                    >
                      Edit Display Name <span>→</span>
                    </button>
                  ) : (
                    <div className="space-y-2">
                      <input
                        type="text"
                        value={nameValue}
                        onChange={e => setNameValue(e.target.value)}
                        placeholder="Your full name"
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveName}
                          disabled={nameLoading}
                          className="flex-1 py-2 px-3 bg-emerald-500 hover:bg-emerald-400 text-slate-900 text-sm font-bold rounded-lg transition-colors disabled:opacity-50"
                        >
                          {nameLoading ? 'Saving…' : 'Save'}
                        </button>
                        <button
                          onClick={() => { setEditingName(false); setNameMsg(null); setNameValue(user?.name || ''); }}
                          className="flex-1 py-2 px-3 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm font-medium rounded-lg transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                  {nameMsg && (
                    <p className={`text-xs font-medium ${nameMsg.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`}>
                      {nameMsg.text}
                    </p>
                  )}

                  {!showPasswordForm ? (
                    <button
                      onClick={() => { setShowPasswordForm(true); setPwMsg(null); }}
                      className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors border border-slate-700 hover:border-slate-600 flex justify-between items-center"
                    >
                      Change Password <span>→</span>
                    </button>
                  ) : (
                    <form onSubmit={handleChangePassword} className="space-y-2 mt-1">
                      <input
                        type="password" placeholder="Current password" value={currentPw}
                        onChange={e => setCurrentPw(e.target.value)} required
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                      />
                      <input
                        type="password" placeholder="New password (min 8 chars)" value={newPw}
                        onChange={e => setNewPw(e.target.value)} required
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                      />
                      <input
                        type="password" placeholder="Confirm new password" value={confirmPw}
                        onChange={e => setConfirmPw(e.target.value)} required
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                      />
                      {pwMsg && (
                        <p className={`text-xs font-medium ${pwMsg.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`}>
                          {pwMsg.text}
                        </p>
                      )}
                      <div className="flex gap-2">
                        <button
                          type="submit" disabled={pwLoading}
                          className="flex-1 py-2 px-3 bg-emerald-500 hover:bg-emerald-400 text-slate-900 text-sm font-bold rounded-lg transition-colors disabled:opacity-50"
                        >
                          {pwLoading ? 'Updating…' : 'Update'}
                        </button>
                        <button
                          type="button" onClick={() => { setShowPasswordForm(false); setPwMsg(null); setCurrentPw(''); setNewPw(''); setConfirmPw(''); }}
                          className="flex-1 py-2 px-3 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm font-medium rounded-lg transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              </motion.section>

              <motion.section
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-32 bg-emerald-500/5 blur-[100px] rounded-full pointer-events-none" />
                <div className="flex justify-between items-start mb-6">
                  <h2 className="text-xl font-bold text-white flex items-center gap-2 z-10">
                    <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Token Wallet
                  </h2>
                  <div className="text-right z-10">
                    <span className="text-xs text-slate-500 block uppercase tracking-wider mb-1">Balance</span>
                    <div className="text-3xl font-black text-emerald-400 font-mono tracking-tight">{tokenBalance || 0}</div>
                  </div>
                </div>

                <button
                  onClick={() => navigate('/subscription')}
                  className="w-full py-3 px-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] mb-6 z-10 relative"
                >
                  Top Up Tokens
                </button>

                <div className="grid grid-cols-2 gap-3 z-10 relative">
                  <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
                    <div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Tokens Spent</div>
                    <div className="text-xl font-black text-fuchsia-400 font-mono">{telemetry.tokensSpent.toLocaleString()}</div>
                  </div>
                  <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
                    <div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Top Category</div>
                    <div className="text-sm font-bold text-white truncate" title={telemetry.topCategory}>{telemetry.topCategory}</div>
                  </div>
                </div>

                <div className="space-y-4 relative z-10 mt-6">
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-2">Recent Ledger Activity</h3>
                  <div className="space-y-3 mt-4">
                    {tokenHistory.length === 0
                      ? <div className="text-sm text-slate-500 italic">No ledger activity yet.</div>
                      : tokenHistory.map(log => (
                        <div key={log.id} className="flex justify-between items-center text-sm">
                          <div className="truncate pr-4">
                            <div className="text-slate-300 font-medium truncate">{log.action}</div>
                            <div className="text-slate-600 text-xs font-mono mt-0.5">{log.date}</div>
                          </div>
                          <div className={`font-mono font-bold shrink-0 ${log.amount > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                            {log.amount > 0 ? '+' : ''}{log.amount}
                          </div>
                        </div>
                      ))
                    }
                  </div>
                </div>
              </motion.section>
            </div>

            <div className="space-y-8 lg:col-span-2">
              <motion.section
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-1">
                      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                      Unlocked Data Access
                    </h2>
                    <p className="text-sm text-slate-400">Products and HS codes you've unlocked with tokens.</p>
                  </div>
                  <button
                    onClick={() => navigate('/subscription')}
                    className="text-sm text-blue-400 hover:text-blue-300 font-medium px-3 py-2 bg-blue-500/10 hover:bg-blue-500/20 rounded-md transition-colors whitespace-nowrap"
                  >
                    Buy More Access
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                        <th className="pb-3 px-2 font-medium">Product / Category</th>
                        <th className="pb-3 px-2 font-medium">Type</th>
                        <th className="pb-3 px-2 font-medium">Unlocked On</th>
                        <th className="pb-3 px-2 font-medium text-right">Tokens Paid</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                      {entitlements.length === 0 ? (
                        <tr>
                          <td colSpan="4" className="py-8 text-center text-slate-500 text-sm">
                            No data unlocked yet. Search for a product and unlock access to see it here.
                          </td>
                        </tr>
                      ) : entitlements.map(item => (
                        <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-4 px-2">
                            <div className="font-medium text-slate-200">{item.name}</div>
                          </td>
                          <td className="py-4 px-2">
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              {item.accessLevel}
                            </span>
                          </td>
                          <td className="py-4 px-2 text-sm text-slate-400 font-mono">{item.purchaseDate}</td>
                          <td className="py-4 px-2 text-right font-mono text-fuchsia-400 font-bold">{item.tokenCost}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.section>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
