import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";

export default function VerifyEmailSuccess() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState("verifying"); 
  const [message, setMessage] = useState("Verifying your email...");

  useEffect(() => {
    
    const queryStatus = searchParams.get('status');

    if (queryStatus) {
      
      switch (queryStatus) {
        case 'verified':
          setStatus("success");
          setMessage("Email verified successfully! You can now login.");
          setTimeout(() => navigate('/login'), 3000);
          break;
        case 'already_verified':
          setStatus("success");
          setMessage("Your email is already verified. You can now login.");
          setTimeout(() => navigate('/login'), 3000);
          break;
        case 'expired':
          setStatus("expired");
          setMessage("Verification link has expired. Please request a new one.");
          break;
        case 'invalid':
          setStatus("error");
          setMessage("Invalid verification link.");
          break;
        default:
          setStatus("error");
          setMessage("Unknown verification status.");
      }
    } else {
      
      setStatus("error");
      setMessage("Verification link is invalid.");
    }
  }, [token, navigate, searchParams]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-100 flex flex-col">
      {}
      <nav className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
        <div className="text-2xl font-bold text-[#1A4D2E]">ZaraiLink</div>
      </nav>

      {}
      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="bg-white w-full max-w-md rounded-2xl shadow-lg p-10 space-y-8">
          {status === "verifying" && (
            <>
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#1A4D2E]"></div>
              </div>
              <h1 className="text-2xl font-bold text-[#1A4D2E] text-center">
                Verifying Your Email
              </h1>
              <p className="text-gray-600 text-center">Please wait while we verify your email address...</p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="flex justify-center">
                <div className="bg-green-100 rounded-full p-4">
                  <svg className="w-16 h-16 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
              <h1 className="text-2xl font-bold text-green-600 text-center">
                Email Verified!
              </h1>
              <p className="text-gray-600 text-center">{message}</p>
              <p className="text-gray-500 text-sm text-center">
                Redirecting to login page in 3 seconds...
              </p>
              <button
                onClick={() => navigate('/login')}
                className="w-full rounded-lg py-3 font-semibold text-white bg-[#1A4D2E] hover:bg-[#163f26] transition"
              >
                Go to Login
              </button>
            </>
          )}

          {status === "error" && (
            <>
              <div className="flex justify-center">
                <div className="bg-red-100 rounded-full p-4">
                  <svg className="w-16 h-16 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
              </div>
              <h1 className="text-2xl font-bold text-red-600 text-center">
                Verification Failed
              </h1>
              <p className="text-gray-600 text-center">{message}</p>
              <button
                onClick={() => navigate('/login')}
                className="w-full rounded-lg py-3 font-semibold text-white bg-[#1A4D2E] hover:bg-[#163f26] transition"
              >
                Go to Login
              </button>
            </>
          )}

          {status === "expired" && (
            <>
              <div className="flex justify-center">
                <div className="bg-yellow-100 rounded-full p-4">
                  <svg className="w-16 h-16 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <h1 className="text-2xl font-bold text-yellow-600 text-center">
                Link Expired
              </h1>
              <p className="text-gray-600 text-center">{message}</p>
              <button
                onClick={() => navigate('/signup')}
                className="w-full rounded-lg py-3 font-semibold text-white bg-[#1A4D2E] hover:bg-[#163f26] transition"
              >
                Request New Verification Email
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
