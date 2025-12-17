import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom"; 

export default function EmailVerification() {
  const location = useLocation(); 
  const navigate = useNavigate(); 

  
  const [email, setEmail] = useState(location.state?.email || ""); 
  const [message, setMessage] = useState(""); 
  const [isResending, setIsResending] = useState(false); 

  
  
  
  
  
  
  
  
  
  

  const handleResendEmail = async () => {
    if (!email) {
      setMessage("No email address found. Please sign up again.");
      return;
    }

    setIsResending(true);
    setMessage(""); 

    try {
      const response = await fetch('http://localhost:8000/accounts/api/resend-verification/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage("Verification email resent successfully!");
      } else {
        setMessage(data.error || "Failed to resend verification email. Please try again.");
      }
    } catch (error) {
      console.error('Resend error:', error);
      setMessage("Network error. Please check your connection and try again.");
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-100 flex flex-col">
      {}
      <nav className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
        <div className="text-2xl font-bold text-[#1A4D2E]">ZaraiLink</div>
        {}
        {}
      </nav>

      {}
      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="bg-white w-full max-w-md rounded-2xl shadow-lg p-10 space-y-8">
          <h1 className="text-3xl font-bold text-[#1A4D2E] text-center">
            Verify Your Email Address
          </h1>
          <p className="text-gray-600 text-center">
            We have sent a verification email to your registered email address.
          </p>

          {}
          {email && (
            <div className="text-center">
              <p className="text-lg font-medium text-gray-800">{email}</p>
            </div>
          )}

          {}
          <div className="space-y-2">
            <p className="text-gray-700">1. Check your email inbox</p>
            <p className="text-gray-700">2. Open the email from ZaraiLink</p>
            <p className="text-gray-700">3. Click on the verification link</p>
          </div>

          {}
          <div className="pt-4">
            <button
              onClick={handleResendEmail}
              disabled={isResending} 
              className={`w-full rounded-lg py-3 font-semibold text-white transition ${
                isResending ? "bg-gray-400 cursor-not-allowed" : "bg-[#1A4D2E] hover:bg-[#163f26]"
              }`}
            >
              {isResending ? "Sending..." : "Resend Verification Email"}
            </button>
          </div>

          {}
          {message && (
            <div className={`text-center text-sm ${message.includes("success") ? "text-green-600" : "text-red-600"}`}>
              {message}
            </div>
          )}

          {}
          <p className="text-gray-600 text-sm text-center">
            Didn't receive the email? Check your spam folder or click resend above.
          </p>
        </div>
      </div>
    </div>
  );
}