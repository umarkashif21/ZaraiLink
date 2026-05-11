import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Globe, TrendingUp, Search, Lock, Shield, 
  BarChart2, Users, ArrowRight, CheckCircle2 
} from 'lucide-react';
import './LandingPage.css';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="landing-page-wrapper min-h-screen bg-slate-50 text-slate-900 font-sans">
      <section className="hero-pattern pt-24 pb-32 px-6 lg:px-8 text-white">
        <div className="max-w-7xl mx-auto relative z-10">
          <nav className="flex items-center justify-between mb-20">
            <div className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center font-bold text-slate-900">
                Z
              </div>
              ZaraiLink
            </div>
            <div className="flex gap-4 items-center">
              <button 
                onClick={() => navigate('/login')}
                className="text-slate-300 hover:text-white font-medium"
              >
                Sign In
              </button>
              <button 
                onClick={() => navigate('/signup')}
                className="bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-5 py-2.5 rounded-full font-bold transition-colors shadow-lg shadow-emerald-500/20"
              >
                Create Account
              </button>
            </div>
          </nav>

          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-tight">
              Trade intelligence for <br className="hidden md:block"/>
              <span className="text-emerald-400">global commodities.</span>
            </h1>
            <p className="text-xl md:text-2xl text-slate-300 mb-12 font-medium max-w-2xl mx-auto">
              Find the right partners. Enter the right markets. Make data-driven sourcing and export decisions.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button 
                onClick={() => navigate('/signup')}
                className="w-full sm:w-auto px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-900 rounded-full font-bold text-lg transition-all shadow-xl shadow-emerald-500/20 flex items-center justify-center gap-2"
              >
                Get Started Free <ArrowRight size={20} />
              </button>
              <button 
                onClick={() => navigate('/signup')}
                className="w-full sm:w-auto px-8 py-4 bg-slate-800 hover:bg-slate-700 text-white border border-slate-600 rounded-full font-bold text-lg transition-all"
              >
                Explore Platform
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-slate-100 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Real-Time Market Signals</h2>
            <p className="text-slate-500 text-lg">Gain unprecedented visibility into global trade flows.</p>
          </div>

          <div className="relative max-w-5xl mx-auto bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="p-8 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center text-blue-600">
                  <TrendingUp size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-lg">Global Wheat Import Volume</h3>
                  <p className="text-sm text-slate-500">Live 30-day tracking index</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-black text-emerald-600">+14.2%</div>
                <div className="text-sm text-slate-500">vs Prev 30 Days</div>
              </div>
            </div>
            
            <div className="p-8 relative">
              <div className="flex items-end justify-between h-64 gap-2 opacity-80">
                {[40, 60, 45, 80, 55, 90, 75, 110, 85, 130, 100, 150].map((h, i) => (
                  <div key={i} className="w-full bg-slate-200 rounded-t-lg relative group">
                    <div 
                      className="absolute bottom-0 w-full bg-blue-500 rounded-t-lg chart-bar-grow"
                      style={{ height: `${h}%`, animationDelay: `${i * 0.1}s` }}
                    ></div>
                  </div>
                ))}
              </div>

              <div className="absolute inset-0 blur-overlay flex flex-col items-center justify-center z-10">
                <div className="bg-slate-900/95 p-8 rounded-2xl shadow-2xl text-center max-w-sm border border-slate-700">
                  <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4 lock-pulse">
                    <Lock className="text-emerald-400" size={28} />
                  </div>
                  <h4 className="text-white text-xl font-bold mb-2">Unlock Market Data</h4>
                  <p className="text-slate-400 text-sm mb-6">Create a free account to view real-time shipment volumes, pricing trends, and complete historical data.</p>
                  <button 
                    onClick={() => navigate('/signup')}
                    className="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-bold py-3 px-4 rounded-xl transition-colors"
                  >
                    Reveal Full Intelligence
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 px-6 max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-xl flex items-center justify-center mb-6">
              <Users size={24} />
            </div>
            <h2 className="text-4xl font-extrabold text-slate-900 mb-6">Discover Verified Trading Partners</h2>
            <p className="text-lg text-slate-600 mb-8 leading-relaxed">
              Stop guessing who you're trading with. Access our proprietary database of thousands of global buyers and suppliers, complete with verified shipment records, trust indicators, and active product portfolios.
            </p>
            <ul className="space-y-4 mb-10">
              {['Verify counterparty authenticity across borders', 'Analyze historical shipment cadence and volumes', 'Discover active buyers for your specific HS codes'].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <CheckCircle2 className="text-emerald-500 shrink-0 mt-0.5" size={20} />
                  <span className="text-slate-700 font-medium">{item}</span>
                </li>
              ))}
            </ul>
            <button 
              onClick={() => navigate('/signup')}
              className="text-emerald-600 font-bold text-lg hover:text-emerald-700 flex items-center gap-2 group"
            >
              Start Finding Buyers <ArrowRight className="group-hover:translate-x-1 transition-transform" size={20}/>
            </button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/10 to-blue-500/10 rounded-3xl transform rotate-3"></div>

            <div className="relative space-y-4">
              <div className="bg-white p-6 rounded-2xl shadow-xl border border-slate-100">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="font-bold text-lg text-slate-900">Alpha Global Traders LLC</h4>
                    <span className="text-sm text-slate-500">United States • Buyer</span>
                  </div>
                  <span className="bg-emerald-100 text-emerald-700 text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                    <Shield size={12} /> Verified
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-50">
                  <div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider">Shipments</div>
                    <div className="font-bold text-slate-900">3,492</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider">Top Product</div>
                    <div className="font-bold text-slate-900">Dextrose</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider">Volume</div>
                    <div className="font-bold text-slate-900">12K MT</div>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-2xl shadow-xl border border-slate-100 relative overflow-hidden">
                <div className="filter blur-[3px] opacity-60">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="font-bold text-lg text-slate-900">Delta Chem International</h4>
                      <span className="text-sm text-slate-500">China • Supplier</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-50">
                    <div>
                      <div className="font-bold text-slate-900">1,204</div>
                    </div>
                  </div>
                </div>
                <div className="absolute inset-0 bg-white/40 flex items-center justify-center">
                  <button onClick={() => navigate('/signup')} className="bg-slate-900 text-white font-bold py-2 px-6 rounded-lg text-sm shadow-lg hover:bg-slate-800">
                    Unlock Profile
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            
            <div className="order-2 lg:order-1 grid grid-cols-2 gap-4">
              <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 transform hover:-translate-y-1 transition-transform">
                <Globe className="text-blue-400 mb-4" size={32} />
                <h4 className="text-4xl font-black mb-2 brand-gradient-text">140+</h4>
                <p className="text-slate-400 font-medium">Countries Tracked</p>
              </div>
              <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 transform translate-y-8 hover:translate-y-6 transition-transform">
                <BarChart2 className="text-emerald-400 mb-4" size={32} />
                <h4 className="text-4xl font-black mb-2 brand-gradient-text">10M+</h4>
                <p className="text-slate-400 font-medium">Shipment Records</p>
              </div>
            </div>

            <div className="order-1 lg:order-2">
              <h2 className="text-4xl font-extrabold mb-6">Unrivaled Market Intelligence</h2>
              <p className="text-lg text-slate-400 mb-8 leading-relaxed">
                Whether you are analyzing macro supply chain shifts or tracking a competitor's export footprint, ZaraiLink gives you the strategic advantage of comprehensive data.
              </p>
              <button 
                onClick={() => navigate('/signup')}
                className="bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-6 py-3 rounded-full font-bold transition-colors"
              >
                Discover New Markets
              </button>
            </div>

          </div>
        </div>
      </section>

      <section className="py-24 bg-slate-50 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-extrabold text-slate-900">Three steps to smarter trade.</h2>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 relative">
            <div className="hidden md:block absolute top-12 left-1/6 right-1/6 h-0.5 bg-slate-200 z-0"></div>

            <div className="relative z-10 bg-white p-8 rounded-2xl shadow-xl border border-slate-100 flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center mb-6 shadow-inner">
                <Search size={28} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">1. Discover</h3>
              <p className="text-slate-600">Search globally by HS code, product name, or specific company to uncover instant trade opportunities.</p>
            </div>

            <div className="relative z-10 bg-white p-8 rounded-2xl shadow-xl border border-slate-100 flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-purple-100 text-purple-600 rounded-2xl flex items-center justify-center mb-6 shadow-inner">
                <BarChart2 size={28} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">2. Evaluate</h3>
              <p className="text-slate-600">Analyze counterparty trust, shipment history, and macro market trends to mitigate risk.</p>
            </div>

            <div className="relative z-10 bg-white p-8 rounded-2xl shadow-xl border border-slate-100 flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mb-6 shadow-inner">
                <Globe size={28} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">3. Connect</h3>
              <p className="text-slate-600">Reach out directly to verified decision-makers and execute trades with absolute confidence.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 border-y border-slate-200 bg-white text-center px-6">
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-10">Trusted by Global Trading Desk Analysts</h3>
        <div className="flex flex-wrap justify-center gap-8 md:gap-16 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
          {['AgriTrade Inc', 'GlobalChem Ports', 'Pacific Sourcing', 'Delta Logistics'].map(name => (
            <div key={name} className="text-2xl font-black font-serif text-slate-800">
              {name}
            </div>
          ))}
        </div>
      </section>

      <section className="py-32 bg-slate-900 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-emerald-500/10 blur-[100px] rounded-full scale-150 transform translate-y-1/2"></div>
        
        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <h2 className="text-5xl font-extrabold mb-6">Stop searching. Start trading.</h2>
          <p className="text-xl text-slate-300 mb-10 max-w-2xl mx-auto">
            Join the platform that gives you an unfair advantage in global commodity markets. Institutional-grade intelligence, accessible to everyone.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <button 
              onClick={() => navigate('/signup')}
              className="px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-900 rounded-full font-bold text-lg transition-transform hover:scale-105 shadow-2xl shadow-emerald-500/20"
            >
              Create Free Account
            </button>
            <button 
              onClick={() => navigate('/login')}
              className="px-8 py-4 bg-transparent hover:bg-slate-800 text-white border border-slate-600 rounded-full font-bold text-lg transition-colors"
            >
              Sign In to Your Account
            </button>
          </div>
        </div>
      </section>
      
      <footer className="bg-slate-950 py-8 text-center text-slate-500 text-sm">
        <p>&copy; {new Date().getFullYear()} ZaraiLink. All rights reserved.</p>
      </footer>
    </div>
  );
}
