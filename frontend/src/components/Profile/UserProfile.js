import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { motion } from 'framer-motion';
import Navbar from '../Layout/Navbar';

const UserProfile = () => {
  const { user, tokenBalance } = useAuth();
  const navigate = useNavigate();

  // Mock data for entitlements and history (since paywall isn't fully implemented yet)
  const mockEntitlements = [
    {
      id: 1,
      name: "Global Supplier Directory API",
      accessLevel: "Full Access",
      purchaseDate: "2024-03-15",
      tokenCost: 500,
      status: "active"
    },
    {
      id: 2,
      name: "Pakistan Export Ledger 2024",
      accessLevel: "Full Access",
      purchaseDate: "2024-04-02",
      tokenCost: 1200,
      status: "active"
    },
    {
      id: 3,
      name: "Real-time Port Alerts (Karachi)",
      accessLevel: "Not Purchased",
      purchaseDate: "-",
      tokenCost: 350,
      status: "inactive"
    }
  ];

  const mockTokenHistory = [
    { id: 1, date: "2024-04-18", action: "Unlock: Dextrose Supplier List", amount: -25 },
    { id: 2, date: "2024-04-15", action: "Token Top-up via Stripe", amount: +1000 },
    { id: 3, date: "2024-04-10", action: "Unlock: Trade Lens Report", amount: -150 }
  ];

  return (
    <div className="min-h-screen bg-slate-950 font-sans selection:bg-emerald-500/30 selection:text-emerald-200">
      <Navbar />
      <div className="text-slate-300 py-12 px-6 lg:px-12">
        <div className="max-w-[1400px] mx-auto space-y-8">
        
        <header className="mb-10">
          <h1 className="text-4xl font-black text-white tracking-tight">Access Management</h1>
          <p className="text-slate-500 mt-2 text-lg">Manage your identity, API entitlements, and token ledger.</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* LEFT COLUMN: Identity & Tokens */}
          <div className="space-y-8 lg:col-span-1">
            
            {/* 1. User Account Section */}
            <motion.section 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
              <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                Identity Profile
              </h2>
              
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-full bg-slate-800 border-2 border-slate-700 flex items-center justify-center text-white font-bold text-xl shadow-inner">
                  {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <div>
                  <div className="text-lg font-bold text-white">{user?.name || 'ZaraiLink User'}</div>
                  <div className="text-sm text-slate-500">{user?.email || 'user@company.com'}</div>
                  <div className="mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5"></span>
                    Active Analyst
                  </div>
                </div>
              </div>

              <div className="space-y-3 pt-4 border-t border-slate-800/50">
                <button 
                  onClick={() => alert("Profile editing functionality coming soon!")}
                  className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors border border-slate-700 hover:border-slate-600 flex justify-between items-center"
                >
                  Edit Profile Information <span>→</span>
                </button>
                <button 
                  onClick={() => alert("Security settings coming soon!")}
                  className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors border border-slate-700 hover:border-slate-600 flex justify-between items-center"
                >
                  Update Security Credentials <span>→</span>
                </button>
              </div>
            </motion.section>

            {/* 2. Token Wallet Section */}
            <motion.section 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden"
            >
               <div className="absolute top-0 right-0 p-32 bg-emerald-500/5 blur-[100px] rounded-full pointer-events-none"></div>
              
              <div className="flex justify-between items-start mb-6 align-top">
                <h2 className="text-xl font-bold text-white flex items-center gap-2 z-10">
                  <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  Token Wallet
                </h2>
                <div className="text-right z-10">
                  <span className="text-xs text-slate-500 block uppercase tracking-wider mb-1">Balance</span>
                  <div className="text-3xl font-black text-emerald-400 font-mono tracking-tight">{tokenBalance || 2450}</div>
                </div>
              </div>

              <button 
                onClick={() => navigate('/subscription')}
                className="w-full py-3 px-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] mb-6 z-10 relative"
              >
                Acquire Tokens
              </button>

              <div className="space-y-4 relative z-10">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-2">Recent Ledger Activity</h3>
                <div className="space-y-3">
                  {mockTokenHistory.map(log => (
                    <div key={log.id} className="flex justify-between items-center text-sm">
                      <div className="truncate pr-4">
                        <div className="text-slate-300 font-medium truncate">{log.action}</div>
                        <div className="text-slate-600 text-xs font-mono mt-0.5">{log.date}</div>
                      </div>
                      <div className={`font-mono font-bold shrink-0 ${log.amount > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                        {log.amount > 0 ? '+' : ''}{log.amount}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.section>

          </div>


          {/* RIGHT COLUMN: Entitlements & Analytics */}
          <div className="space-y-8 lg:col-span-2">
            
            {/* 3. Product Access / Entitlements Section */}
            <motion.section 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-1">
                    <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                    Platform Entitlements
                  </h2>
                  <p className="text-sm text-slate-400">
                    Your activated data packages and APIs. Purchase additional access levels using tokens.
                  </p>
                </div>
                <button 
                  onClick={() => navigate('/subscription')}
                  className="text-sm text-blue-400 hover:text-blue-300 font-medium px-3 py-2 bg-blue-500/10 hover:bg-blue-500/20 rounded-md transition-colors whitespace-nowrap"
                >
                  Browse Product Catalog
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                      <th className="pb-3 px-2 font-medium">Data Asset</th>
                      <th className="pb-3 px-2 font-medium">Clearance</th>
                      <th className="pb-3 px-2 font-medium">Activation</th>
                      <th className="pb-3 px-2 font-medium text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {mockEntitlements.map(item => (
                      <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-4 px-2">
                          <div className="font-medium text-slate-200">{item.name}</div>
                          {item.status === 'inactive' && <div className="text-xs text-slate-500 mt-1 font-mono">Unlock Cost: {item.tokenCost} Tokens</div>}
                        </td>
                        <td className="py-4 px-2">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${
                            item.status === 'active' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'
                          }`}>
                            {item.accessLevel}
                          </span>
                        </td>
                        <td className="py-4 px-2 text-sm text-slate-400 font-mono">
                          {item.purchaseDate}
                        </td>
                        <td className="py-4 px-2 text-right">
                          {item.status === 'active' ? (
                            <button className="text-sm font-medium text-slate-400 hover:text-white px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 transition-colors border border-slate-700">
                              Access Data
                            </button>
                          ) : (
                            <button className="text-sm font-bold text-slate-950 bg-emerald-500 hover:bg-emerald-400 px-3 py-1.5 rounded transition-colors shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                              Unlock Access
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.section>

            {/* 4. Platform Usage Summary (Optional Analytics Section) */}
            <motion.section 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl"
            >
              <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                <svg className="w-5 h-5 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                Telemetry & Analytics
              </h2>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                  <div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">Queries</div>
                  <div className="text-2xl font-black text-white font-mono">1,248</div>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                  <div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">Products Viewed</div>
                  <div className="text-2xl font-black text-white font-mono">142</div>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                  <div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">Tokens Spent</div>
                  <div className="text-2xl font-black text-fuchsia-400 font-mono">3,450</div>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                  <div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">Top Category</div>
                  <div className="text-lg font-bold text-white truncate">1702 (Sugars)</div>
                </div>
              </div>
            </motion.section>

             {/* 5. Settings Section */}
             <motion.section 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="mt-8 pt-8 border-t border-slate-800/50"
            >
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-4">System Configurations</h3>
              <div className="flex flex-wrap gap-3">
                <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-md border border-slate-700 transition-colors">
                  Notification Settings
                </button>
                <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-md border border-slate-700 transition-colors">
                  Data Privacy Preferences
                </button>
                <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-md border border-slate-700 transition-colors">
                  Export Audit Log
                </button>
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
