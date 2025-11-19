import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(''); // For success/error messages
  const [showSuccess, setShowSuccess] = useState(false); // To conditionally render success screen

  const navigate = useNavigate(); // For navigation after submission

  const validate = () => {
    const newErrors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim()) newErrors.email = 'Email is required';
    else if (!emailRegex.test(email)) newErrors.email = 'Invalid email format';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setMessage('');

    // Simulate API call to send password reset email
    console.log('Sending password reset email to:', email);
    setTimeout(() => {
      setLoading(false);
      setMessage('Password reset email sent successfully! Please check your inbox.');
      setShowSuccess(true);
    }, 1500);
  };

  // Logo-only navbar
  const Navbar = () => (
    <nav className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
      <div className="text-2xl font-bold text-[#1A4D2E]">ZaraiLink</div>
    </nav>
  );

  if (showSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-100 flex flex-col">
        <Navbar />

        <div className="flex-1 flex items-center justify-center px-6 py-10">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-lg p-10 space-y-8">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
                <svg
                  className="h-10 w-10 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M5 13l4 4L19 7"
                  ></path>
                </svg>
              </div>
              <h1 className="text-3xl font-bold text-[#1A4D2E] mt-4">Check your email</h1>
              <p className="text-gray-600 mt-2">
                We sent a password reset link to <span className="font-medium">{email}</span>
              </p>
            </div>
            <p className="text-gray-600 text-sm text-center">
              Didn’t receive the email? Check your spam folder or{' '}
              <button
                onClick={() => setShowSuccess(false)}
                className="text-[#1A4D2E] font-medium hover:underline"
              >
                click here to resend
              </button>
              .
            </p>
            <div className="pt-4">
              <button
                onClick={() => navigate('/login')}
                className="w-full rounded-lg py-3 font-semibold text-white bg-[#1A4D2E] hover:bg-[#163f26] transition"
              >
                Back to Sign In
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-100 flex flex-col">
      <Navbar />

      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="bg-white w-full max-w-md rounded-2xl shadow-lg p-10 space-y-8">
          <h1 className="text-3xl font-bold text-[#1A4D2E] text-center">
            Forgot your password?
          </h1>
          <p className="text-gray-600 text-center">
            Enter your email address and we'll send you a link to reset your password.
          </p>

          {message && !showSuccess && (
            <div
              className={`text-center text-sm ${
                message.includes('success') ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {message}
            </div>
          )}

          {!showSuccess && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-gray-700 font-medium mb-1">
                  Work Email
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={`w-full border rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-200 ${
                    errors.email ? 'border-red-500' : ''
                  }`}
                  placeholder="Enter your work email"
                />
                {errors.email && <p className="text-red-600 text-sm mt-1">{errors.email}</p>}
              </div>

              <button
                type="submit"
                disabled={loading}
                className={`w-full rounded-lg py-3 font-semibold text-white transition ${
                  loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-[#1A4D2E] hover:bg-[#163f26]'
                }`}
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
          )}

          <p className="text-center text-gray-600 text-sm">
            Remember your password?{' '}
            <Link to="/login" className="text-[#1A4D2E] font-medium hover:underline">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
