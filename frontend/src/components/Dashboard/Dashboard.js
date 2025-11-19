import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-100 flex flex-col">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
        <div className="text-2xl font-bold text-[#1A4D2E]">ZaraiLink</div>
        <div className="flex items-center space-x-4">
          <span className="text-gray-700">Welcome, {user?.name || user?.email}!</span>
          <button
            onClick={handleLogout}
            className="bg-[#1A4D2E] text-white px-4 py-2 rounded-lg hover:bg-[#163f26] transition"
          >
            Logout
          </button>
        </div>
      </nav>

      {/* Main Dashboard Content */}
      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="bg-white w-full max-w-4xl rounded-2xl shadow-lg p-10 space-y-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-[#1A4D2E] mb-4">
              Welcome to ZaraiLink Dashboard
            </h1>
            <p className="text-gray-600 text-lg">
              Your Gateway to Pakistan's Verified Trade Intelligence
            </p>
          </div>

          {/* User Info Card */}
          <div className="bg-green-50 rounded-lg p-6 space-y-3">
            <h2 className="text-2xl font-semibold text-[#1A4D2E] mb-3">Your Account</h2>
            <div className="space-y-2">
              <p className="text-gray-700">
                <span className="font-medium">Name:</span> {user?.name || 'Not provided'}
              </p>
              <p className="text-gray-700">
                <span className="font-medium">Email:</span> {user?.email}
              </p>
              <p className="text-gray-700">
                <span className="font-medium">Status:</span>{' '}
                <span className={user?.email_verified ? 'text-green-600' : 'text-yellow-600'}>
                  {user?.email_verified ? ' Verified' : 'Pending Verification'}
                </span>
              </p>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
            <div className="bg-white border-2 border-green-200 rounded-lg p-6 hover:shadow-md transition">
              <h3 className="text-xl font-semibold text-[#1A4D2E] mb-2">Trade Directory</h3>
              <p className="text-gray-600">
                Access verified suppliers and buyers across Pakistan's agricultural sector.
              </p>
            </div>
            <div className="bg-white border-2 border-green-200 rounded-lg p-6 hover:shadow-md transition">
              <h3 className="text-xl font-semibold text-[#1A4D2E] mb-2">Market Intelligence</h3>
              <p className="text-gray-600">
                Get real-time insights on commodity prices and market trends.
              </p>
            </div>
            <div className="bg-white border-2 border-green-200 rounded-lg p-6 hover:shadow-md transition">
              <h3 className="text-xl font-semibold text-[#1A4D2E] mb-2">Analytics Dashboard</h3>
              <p className="text-gray-600">
                Visualize trade patterns and identify business opportunities.
              </p>
            </div>
            <div className="bg-white border-2 border-green-200 rounded-lg p-6 hover:shadow-md transition">
              <h3 className="text-xl font-semibold text-[#1A4D2E] mb-2">Subscription Plans</h3>
              <p className="text-gray-600">
                Upgrade your account to unlock premium features and unlimited access.
              </p>
            </div>
          </div>

          {/* Call to Action */}
          <div className="text-center mt-8">
            <p className="text-gray-600 mb-4">
              This is a demonstration dashboard. Full features coming soon!
            </p>
            <button className="bg-[#1A4D2E] text-white px-6 py-3 rounded-lg hover:bg-[#163f26] transition font-semibold">
              Explore Features
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
