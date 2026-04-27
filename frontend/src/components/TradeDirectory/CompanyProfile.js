import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { motion } from 'framer-motion';
import Navbar from '../Layout/Navbar';
import {
  UnlockConfirmModal,
  SuccessModal,
  InsufficientTokensModal,
  ErrorModal,
} from '../Common/Modal';

const API = process.env.REACT_APP_API_BASE_URL;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getCookie(name) {
  const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
  return v ? v[2] : null;
}

/** Derive a seniority label from the designation string */
function getSeniorityBadge(designation = '') {
  const d = designation.toLowerCase();
  if (d.includes('ceo') || d.includes('chief') || d.includes('director') || d.includes('owner') || d.includes('partner') || d.includes('president'))
    return { label: 'Decision Maker', color: 'bg-amber-100 text-amber-700 border-amber-200' };
  if (d.includes('procure') || d.includes('purchase') || d.includes('supply') || d.includes('buyer'))
    return { label: 'Procurement', color: 'bg-blue-100 text-blue-700 border-blue-200' };
  if (d.includes('sales') || d.includes('export') || d.includes('business dev') || d.includes('marketing'))
    return { label: 'Sales', color: 'bg-emerald-100 text-emerald-700 border-emerald-200' };
  if (d.includes('manager') || d.includes('head') || d.includes('lead'))
    return { label: 'Management', color: 'bg-indigo-100 text-indigo-700 border-indigo-200' };
  return { label: 'Team Member', color: 'bg-slate-100 text-slate-600 border-slate-200' };
}

/** Mask locked value: show partial number hint */
function maskValue(val) {
  if (!val || val.includes('Locked')) {
    // Generic blur placeholder
    return '•••• •••• ••••';
  }
  if (val.includes('@')) {
    const [user, domain] = val.split('@');
    return `${user[0]}${'•'.repeat(Math.min(user.length - 1, 5))}@${domain}`;
  }
  // Phone — show country code + mask the rest
  const clean = val.replace(/\D/g, '');
  return `+${clean.slice(0, 2)} ${'•'.repeat(4)}-${'•'.repeat(7)}`;
}

// ─── Contact Card ─────────────────────────────────────────────────────────────

const ContactCard = ({ contact, onUnlock, unlocking }) => {
  const { label, color } = getSeniorityBadge(contact.designation);
  const isUnlocked = contact.is_unlocked || contact.is_public;
  const initial = contact.name?.charAt(0)?.toUpperCase() || '?';

  const channels = [
    { key: 'phone', icon: '📞', label: 'Phone' },
    { key: 'email', icon: '📧', label: 'Email' },
    { key: 'whatsapp', icon: '💬', label: 'WhatsApp' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={`relative bg-white rounded-2xl border-2 shadow-sm overflow-hidden transition-all ${
        isUnlocked ? 'border-emerald-200 shadow-emerald-50' : 'border-slate-200 hover:border-slate-300'
      }`}
    >
      {/* Unlocked top bar */}
      {isUnlocked && (
        <div className="h-1 w-full bg-gradient-to-r from-emerald-400 to-teal-400" />
      )}

      <div className="p-5">
        {/* Header row */}
        <div className="flex items-start gap-4 mb-4">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold flex-shrink-0 ${
            isUnlocked
              ? 'bg-gradient-to-br from-emerald-500 to-teal-500 text-white'
              : 'bg-slate-100 text-slate-500'
          }`}>
            {initial}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-slate-900 text-base">{contact.name}</span>
              {contact.is_public && (
                <span className="text-xs font-medium bg-teal-50 text-teal-700 border border-teal-200 px-2 py-0.5 rounded-full">
                  Public
                </span>
              )}
              {contact.is_unlocked && !contact.is_public && (
                <span className="text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">
                  ✓ Unlocked
                </span>
              )}
            </div>
            {contact.designation && (
              <p className="text-sm text-slate-500 mt-0.5">{contact.designation}</p>
            )}
            <span className={`mt-1.5 inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full border ${color}`}>
              {label}
            </span>
          </div>
        </div>

        {/* Channel availability (always visible) */}
        <div className="flex gap-2 mb-4">
          {channels.map(ch => {
            const hasChannel = contact[ch.key] && !contact[ch.key].includes('Locked');
            return (
              <div
                key={ch.key}
                title={ch.label}
                className={`flex items-center gap-1 text-xs px-2 py-1 rounded-lg border font-medium ${
                  hasChannel || isUnlocked
                    ? 'bg-slate-50 border-slate-200 text-slate-600'
                    : 'bg-slate-50 border-slate-100 text-slate-300'
                }`}
              >
                <span>{ch.icon}</span>
                <span>{ch.label}</span>
              </div>
            );
          })}
        </div>

        {/* Contact details */}
        <div className="space-y-2">
          {channels.map(ch => {
            if (ch.key === 'whatsapp' && !contact.whatsapp) return null;
            return (
              <div key={ch.key} className="flex items-center gap-3">
                <span className="text-slate-400 text-sm w-14 flex-shrink-0 font-medium">{ch.label}</span>
                {isUnlocked ? (
                  <span className="text-slate-800 text-sm font-mono font-semibold">
                    {contact[ch.key] || '—'}
                  </span>
                ) : (
                  <span className="text-slate-300 text-sm font-mono tracking-widest blur-[3px] select-none">
                    {maskValue(contact[ch.key])}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Unlock CTA */}
        {!isUnlocked && (
          <button
            onClick={() => onUnlock(contact)}
            disabled={unlocking}
            className="mt-5 w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-white font-bold rounded-xl transition-all shadow-md shadow-emerald-500/20 hover:shadow-emerald-500/40 hover:-translate-y-0.5 disabled:opacity-60 disabled:translate-y-0"
          >
            <span>🔓</span>
            {unlocking ? 'Unlocking…' : 'Unlock Contact Details'}
            <span className="ml-1 text-xs font-normal bg-white/20 px-1.5 py-0.5 rounded-full">1 token</span>
          </button>
        )}
      </div>
    </motion.div>
  );
};

// ─── Main Component ────────────────────────────────────────────────────────────

const CompanyProfile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { tokenBalance, refreshUser } = useAuth();

  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedContact, setSelectedContact] = useState(null);
  const [unlocking, setUnlocking] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [showInsufficientTokensModal, setShowInsufficientTokensModal] = useState(false);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [unlockedContactData, setUnlockedContactData] = useState(null);

  useEffect(() => { loadCompanyData(); }, [id]);

  const loadCompanyData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/companies/${id}/`, { credentials: 'include' });
      if (res.ok) setCompany(await res.json());
      else if (res.status === 404) setError('Company not found');
      else throw new Error('Failed to load');
    } catch {
      setError('Failed to load company. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUnlockClick = (contact) => {
    if (contact.is_unlocked || contact.is_public) return;
    setSelectedContact(contact);
    setShowConfirmModal(true);
  };

  const handleConfirmUnlock = async () => {
    setShowConfirmModal(false);
    setUnlocking(true);
    try {
      const csrftoken = getCookie('csrftoken');
      const res = await fetch(`${API}/api/key-contacts/${selectedContact.id}/unlock/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        credentials: 'include',
      });
      const data = await res.json();
      if (res.ok) {
        await refreshUser();
        setUnlockedContactData(data.contact);
        setShowSuccessModal(true);
        setTimeout(() => loadCompanyData(), 500);
      } else {
        if (data.status === 'insufficient_tokens' || res.status === 402) {
          setShowInsufficientTokensModal(true);
        } else {
          setErrorMessage(data.message || 'Failed to unlock contact');
          setShowErrorModal(true);
        }
      }
    } catch {
      setErrorMessage('Network error. Please check your connection.');
      setShowErrorModal(true);
    } finally {
      setUnlocking(false);
    }
  };

  // ── Loading / Error states ────────────────────────────────────────────────
  if (loading) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 font-medium text-sm">Loading company profile…</p>
      </div>
    </div>
  );

  if (error || !company) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="text-center">
        <p className="text-slate-500 mb-4">{error || 'Company not found'}</p>
        <button onClick={() => navigate('/trade-directory/find-suppliers')} className="px-5 py-2 bg-emerald-500 text-white rounded-xl font-bold">
          Back to Directory
        </button>
      </div>
    </div>
  );

  const contacts = company.key_contacts || [];
  const unlockedCount = contacts.filter(c => c.is_unlocked || c.is_public).length;

  return (
    <>
      <div className="min-h-screen bg-slate-50 font-sans">
        <Navbar />

        {/* ── Hero Header ─────────────────────────────────────────────── */}
        <div className="bg-white border-b border-slate-200 shadow-sm">
          <div className="max-w-5xl mx-auto px-6 py-8">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-700 font-medium mb-5 transition-colors"
            >
              ← Back to Directory
            </button>
            <div className="flex items-start gap-5">
              {/* Company initial avatar */}
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center text-white font-black text-2xl flex-shrink-0 shadow-lg">
                {company.name?.charAt(0)?.toUpperCase()}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="text-2xl font-black text-slate-900 tracking-tight">{company.name}</h1>
                  {contacts.length > 0 && company.verification_status === 'verified' && (
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full border bg-emerald-50 text-emerald-700 border-emerald-200">
                      ✓ Verified
                    </span>
                  )}
                </div>
                {company.legal_name && company.legal_name !== company.name && (
                  <p className="text-sm text-slate-400 mt-0.5">{company.legal_name}</p>
                )}
                <p className="text-slate-500 mt-1 text-sm">
                  📍 {[company.district, company.province, company.country].filter(Boolean).join(', ')}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Main content ─────────────────────────────────────────────── */}
        <div className="max-w-5xl mx-auto px-6 py-10 space-y-10">

          {/* About + Quick Stats */}
          <section>
            {company.description && (
              <p className="text-slate-600 leading-relaxed mb-6 max-w-3xl">{company.description}</p>
            )}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {[
                { label: 'Sector', value: company.sector?.name },
                { label: 'Role', value: company.company_role?.name },
                { label: 'Type', value: company.company_type?.name },
                { label: 'Established', value: company.year_established },
                { label: 'Employees', value: company.number_of_employees },
                { label: 'Contacts', value: `${contacts.length} (${unlockedCount} unlocked)` },
              ].filter(s => s.value).map(stat => (
                <div key={stat.label} className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">{stat.label}</p>
                  <p className="text-sm font-bold text-slate-800">{stat.value}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 flex gap-3 flex-wrap">
              {company.website && (
                <a href={company.website} target="_blank" rel="noopener noreferrer"
                  className="text-sm text-emerald-600 hover:text-emerald-700 font-semibold flex items-center gap-1">
                  🌐 Visit Website →
                </a>
              )}
              {company.contact_email && (
                <a href={`mailto:${company.contact_email}`}
                  className="text-sm text-emerald-600 hover:text-emerald-700 font-semibold flex items-center gap-1">
                  ✉️ {company.contact_email}
                </a>
              )}
            </div>
          </section>

          {/* Products */}
          {company.products && company.products.length > 0 && (
            <section>
              <h2 className="text-lg font-bold text-slate-700 mb-3">Products Dealt In</h2>
              <div className="flex flex-wrap gap-2">
                {company.products.map(p => (
                  <div key={p.id} className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-xl px-3 py-1.5 shadow-sm">
                    <span className="text-sm font-semibold text-slate-700">{p.name}</span>
                    {p.variety && <span className="text-xs text-slate-400">· {p.variety}</span>}
                    {p.value_added && (
                      <span className="text-xs bg-amber-100 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded-full font-medium">Value Added</span>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ── KEY CONTACTS — Hero Section ──────────────────────────── */}
          <section>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-xl font-black text-slate-900">Key Contacts</h2>
                <p className="text-sm text-slate-400 mt-0.5">
                  {contacts.length === 0
                    ? 'No contacts listed for this company.'
                    : unlockedCount === contacts.length
                    ? `All ${contacts.length} contacts unlocked ✓`
                    : `${unlockedCount} of ${contacts.length} contacts unlocked · 1 token each`}
                </p>
              </div>
              {contacts.length > 0 && unlockedCount < contacts.length && (
                <div className="text-right hidden sm:block">
                  <p className="text-xs text-slate-400">Your balance</p>
                  <p className="text-xl font-black text-emerald-500 font-mono">{tokenBalance || 0}</p>
                  <p className="text-xs text-slate-400">tokens</p>
                </div>
              )}
            </div>

            {contacts.length === 0 ? (
              <div className="bg-white border-2 border-dashed border-slate-200 rounded-2xl p-10 text-center text-slate-400">
                <p className="text-4xl mb-3">👤</p>
                <p className="font-semibold text-slate-500">No key contacts listed yet.</p>
                <p className="text-sm mt-1">Check back later or contact us to request verification.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {contacts.map(contact => (
                  <ContactCard
                    key={contact.id}
                    contact={contact}
                    onUnlock={handleUnlockClick}
                    unlocking={unlocking}
                  />
                ))}
              </div>
            )}

            {/* Low balance nudge */}
            {contacts.length > 0 && unlockedCount < contacts.length && tokenBalance < 1 && (
              <div className="mt-5 flex items-center justify-between bg-amber-50 border border-amber-200 rounded-xl px-5 py-3">
                <p className="text-sm font-medium text-amber-800">You need tokens to unlock contacts.</p>
                <button onClick={() => navigate('/subscription')} className="text-sm font-bold text-amber-700 hover:text-amber-900 underline">
                  Top up →
                </button>
              </div>
            )}
          </section>

        </div>
      </div>

      {/* Modals */}
      <UnlockConfirmModal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        onConfirm={handleConfirmUnlock}
        contactName={selectedContact?.name}
        tokenCost={1}
      />
      <SuccessModal
        isOpen={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        contactInfo={unlockedContactData || {}}
        tokensRemaining={tokenBalance}
      />
      <InsufficientTokensModal
        isOpen={showInsufficientTokensModal}
        onClose={() => setShowInsufficientTokensModal(false)}
        currentBalance={tokenBalance}
        required={1}
        onBuyTokens={() => { setShowInsufficientTokensModal(false); navigate('/subscription'); }}
      />
      <ErrorModal
        isOpen={showErrorModal}
        onClose={() => setShowErrorModal(false)}
        errorMessage={errorMessage}
      />
    </>
  );
};

export default CompanyProfile;
