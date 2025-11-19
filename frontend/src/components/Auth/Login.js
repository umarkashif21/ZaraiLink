// frontend/src/components/Auth/Login.js
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom'; // Import Link and useNavigate
import { useAuth } from '../../context/AuthContext';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate(); // Get the navigate function
  const { login } = useAuth();

  const validate = () => {
    const newErrors = {};
    if (!email.trim()) newErrors.email = "Email is required";
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (email.trim() && !emailRegex.test(email)) newErrors.email = "Invalid email format";
    if (!password) newErrors.password = "Password is required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});

    try {
      const result = await login(email, password);

      if (result.success) {
        // Successfully logged in, redirect to dashboard
        navigate('/dashboard');
      } else {
        // Handle errors
        if (result.email_not_verified) {
          setErrors({
            general: result.error || 'Please verify your email address before logging in.',
            email_not_verified: true
          });
        } else {
          setErrors({ general: result.error || 'Invalid email or password. Please try again.' });
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      setErrors({ general: 'An unexpected error occurred. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-100 flex flex-col">
      {/* --- Navigation Bar (Same as Signup) --- */}
      <nav className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
        <div className="text-2xl font-bold text-[#1A4D2E]">ZaraiLink</div>
        <Link to="/signup" className="text-[#1A4D2E] font-medium hover:underline">
          Sign Up
        </Link>
      </nav>

      {/* --- Main Login Content --- */}
      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="bg-white w-full max-w-md rounded-2xl shadow-lg p-10 space-y-8">
          {/* --- Header --- */}
          <div className="text-center">
            <h1 className="text-3xl font-bold text-[#1A4D2E] mb-2">
              Welcome to ZaraiLink!
            </h1>
            <p className="text-gray-600">
              Your Gateway to Pakistan’s Verified Trade Intelligence
            </p>
          </div>

          {/* --- Login Form --- */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* General Error Message */}
            {errors.general && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {errors.general}
                {errors.email_not_verified && (
                  <div className="mt-2">
                    <Link to="/verify-email" className="underline font-medium">
                      Resend verification email
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-gray-700 font-medium mb-1">
                Email
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={`w-full border rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-200 ${errors.email ? 'border-red-500' : ''}`}
                placeholder="Enter your work email"
              />
              {errors.email && <p className="text-red-600 text-sm mt-1">{errors.email}</p>}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-gray-700 font-medium mb-1">
                Password
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`w-full border rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-200 ${errors.password ? 'border-red-500' : ''}`}
                placeholder="Enter your password"
              />
              {errors.password && <p className="text-red-600 text-sm mt-1">{errors.password}</p>}
            </div>

            {/* Forgot Password Link */}
            <div className="text-right">
              <Link
                to="/forgot-password" // Link to ForgotPassword.js
                className="text-sm text-[#1A4D2E] font-medium hover:underline"
              >
                Forgot Password?
              </Link>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full rounded-lg py-3 font-semibold text-white transition ${
                loading ? "bg-gray-400 cursor-not-allowed" : "bg-[#1A4D2E] hover:bg-[#163f26]"
              }`}
            >
              {loading ? "Logging in..." : "Sign In"}
            </button>
          </form>

          {/* --- Sign Up Link --- */}
          <p className="text-center text-gray-600 text-sm">
            Don't have an account?{" "}
            <Link to="/signup" className="text-[#1A4D2E] font-medium hover:underline">
              Sign Up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;