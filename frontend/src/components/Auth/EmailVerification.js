import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom"; // Import useLocation to get state

export default function EmailVerification() {
  const location = useLocation(); // To access state passed from Signup
  const navigate = useNavigate(); // To navigate if needed (e.g., back to login)

  // Get the email from the location state passed from Signup
  const [email, setEmail] = useState(location.state?.email || ""); // Fallback to empty string if not passed
  const [message, setMessage] = useState(""); // To show success/error messages
  const [isResending, setIsResending] = useState(false); // To handle resend button state

  // Optional: Add a timer to simulate initial check if email was already verified
  // useEffect(() => {
  //   // Simulate an API call to check verification status
  //   // setMessage("Checking verification status...");
  //   // setTimeout(() => {
  //   //   setMessage("Email already verified!");
  //   //   // Redirect to login after a delay
  //   //   // setTimeout(() => navigate('/login'), 2000);
  //   // }, 1000);
  // }, [navigate]);

  const handleResendEmail = () => {
    if (!email) {
      setMessage("No email address found. Please sign up again.");
      return;
    }

    setIsResending(true);
    setMessage(""); // Clear previous messages

    // Simulate API call to resend verification email
    // Replace this with your actual API call
    console.log("Resending verification email to:", email);
    setTimeout(() => {
      setIsResending(false);
      setMessage("Verification email resent successfully!");
      // Optionally, clear the message after a few seconds
      // setTimeout(() => setMessage(""), 3000);
    }, 1500); // Simulate API delay
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-100 flex flex-col">
      {/* Navbar - Keep it minimal or consistent with other auth pages */}
      <nav className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
        <div className="text-2xl font-bold text-[#1A4D2E]">ZaraiLink</div>
        {/* Optionally, add a link to sign in if they already verified */}
        {/* <button className="text-[#1A4D2E] font-medium hover:underline" onClick={() => navigate('/login')}>
          Sign In
        </button> */}
      </nav>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="bg-white w-full max-w-md rounded-2xl shadow-lg p-10 space-y-8">
          <h1 className="text-3xl font-bold text-[#1A4D2E] text-center">
            Verify Your Email Address
          </h1>
          <p className="text-gray-600 text-center">
            We have sent a verification email to your registered email address.
          </p>

          {/* Display the email address */}
          {email && (
            <div className="text-center">
              <p className="text-lg font-medium text-gray-800">{email}</p>
            </div>
          )}

          {/* Instructions */}
          <div className="space-y-2">
            <p className="text-gray-700">1. Check your email inbox</p>
            <p className="text-gray-700">2. Open the email from ZaraiLink</p>
            <p className="text-gray-700">3. Click on the verification link</p>
          </div>

          {/* Resend Button */}
          <div className="pt-4">
            <button
              onClick={handleResendEmail}
              disabled={isResending} // Disable while resending
              className={`w-full rounded-lg py-3 font-semibold text-white transition ${
                isResending ? "bg-gray-400 cursor-not-allowed" : "bg-[#1A4D2E] hover:bg-[#163f26]"
              }`}
            >
              {isResending ? "Sending..." : "Resend Verification Email"}
            </button>
          </div>

          {/* Message Display (Success/Error) */}
          {message && (
            <div className={`text-center text-sm ${message.includes("success") ? "text-green-600" : "text-red-600"}`}>
              {message}
            </div>
          )}

          {/* Info Text */}
          <p className="text-gray-600 text-sm text-center">
            Didn't receive the email? Check your spam folder or click resend above.
          </p>
        </div>
      </div>
    </div>
  );
}