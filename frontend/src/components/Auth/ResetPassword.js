
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom'; 

const ResetPassword = () => {
  const { token } = useParams(); 
  const navigate = useNavigate(); 

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(''); 
  const [showSuccess, setShowSuccess] = useState(false); 
  const [passwordStrength, setPasswordStrength] = useState('');
  const [showPassword, setShowPassword] = useState(false); 
  const [showConfirmPassword, setShowConfirmPassword] = useState(false); 

  
  const calculatePasswordStrength = (password) => {
    if (password.length === 0) return '';
    if (password.length < 6) return 'Too Short';
    if (password.length < 8) return 'Weak';
    if (/[A-Z]/.test(password) && /[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password)) {
      return 'Strong';
    }
    if (/[A-Z]/.test(password) && /[0-9]/.test(password)) {
      return 'Moderate';
    }
    return 'Weak';
  };

  useEffect(() => {
    setPasswordStrength(calculatePasswordStrength(newPassword));
  }, [newPassword]);

  const validate = () => {
    const newErrors = {};
    if (!newPassword) newErrors.newPassword = 'New password is required';
    if (!confirmPassword) newErrors.confirmPassword = 'Confirmation password is required';
    if (newPassword && confirmPassword && newPassword !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setMessage(''); 

    
    
    
    console.log('Resetting password with token:', token, 'and new password:', newPassword);
    
    

    
    setTimeout(() => {
      setLoading(false);
      
      setMessage('Password updated successfully!');
      setShowSuccess(true);
      
      
    }, 1500); 
  };

  if (showSuccess) {
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-100 flex flex-col">
        {}
        <nav className="bg-white shadow-sm px-6 py-4 flex justify-center items-center"> {}
          <div className="text-2xl font-bold text-[#1A4D2E]">ZaraiLink</div>
        </nav>

        {}
        <div className="flex-1 flex items-center justify-center px-6 py-10">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-lg p-10 space-y-8">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
                {}
                <svg className="h-10 w-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                </svg>
              </div>
              <h1 className="text-3xl font-bold text-[#1A4D2E] mt-4">Password Updated!</h1>
              <p className="text-gray-600 mt-2">
                Your password has been successfully reset.
              </p>
            </div>
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
      {}
      <nav className="bg-white shadow-sm px-6 py-4 flex justify-center items-center"> {}
        <div className="text-2xl font-bold text-[#1A4D2E]">ZaraiLink</div>
      </nav>

      {}
      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="bg-white w-full max-w-md rounded-2xl shadow-lg p-10 space-y-8">
          <h1 className="text-3xl font-bold text-[#1A4D2E] text-center">
            Set a new password for your account
          </h1>
          <p className="text-gray-600 text-center">
            Please enter your new password.
          </p>

          {}
          {message && !showSuccess && (
            <div className={`text-center text-sm ${message.includes('success') ? 'text-green-600' : 'text-red-600'}`}>
              {message}
            </div>
          )}

          {}
          {!showSuccess && (
            <form onSubmit={handleSubmit} className="space-y-6">
              {}
              <div>
                <label htmlFor="newPassword" className="block text-gray-700 font-medium mb-1">
                  New Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"} 
                    id="newPassword"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className={`w-full border rounded-lg px-4 py-3 pr-10 focus:ring-2 focus:ring-green-200 ${errors.newPassword ? 'border-red-500' : ''}`} 
                    placeholder="Enter your new password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)} 
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500"
                  >
                    {showPassword ? (
                      
                      <svg className="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path>
                      </svg>
                    ) : (
                      
                      <svg className="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                      </svg>
                    )}
                  </button>
                </div>
                {passwordStrength && (
                  <p className={`text-sm mt-1 ${
                    passwordStrength === 'Strong' ? 'text-green-600' :
                    passwordStrength === 'Moderate' ? 'text-yellow-600' :
                    passwordStrength === 'Weak' ? 'text-orange-600' :
                    'text-red-600' // Includes 'Too Short'
                  }`}>
                    Strength: {passwordStrength}
                  </p>
                )}
                {errors.newPassword && <p className="text-red-600 text-sm mt-1">{errors.newPassword}</p>}
              </div>

              {}
              <div>
                <label htmlFor="confirmPassword" className="block text-gray-700 font-medium mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    type={showConfirmPassword ? "text" : "password"} 
                    id="confirmPassword"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`w-full border rounded-lg px-4 py-3 pr-10 focus:ring-2 focus:ring-green-200 ${errors.confirmPassword ? 'border-red-500' : ''}`} 
                    placeholder="Re-enter your new password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)} 
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500"
                  >
                    {showConfirmPassword ? (
                      
                      <svg className="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path>
                      </svg>
                    ) : (
                      
                      <svg className="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                      </svg>
                    )}
                  </button>
                </div>
                {errors.confirmPassword && <p className="text-red-600 text-sm mt-1">{errors.confirmPassword}</p>}
              </div>

              {}
              <button
                type="submit"
                disabled={loading}
                className={`w-full rounded-lg py-3 font-semibold text-white transition ${
                  loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-[#1A4D2E] hover:bg-[#163f26]'
                }`}
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;