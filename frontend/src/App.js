
/*
import Signup from "./components/Auth/Signup";

function App() {
  return <Signup />;
}

export default App;
*/

import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Signup from "./components/Auth/Signup";
import Login from "./components/Auth/Login";
import ForgotPassword from "./components/Auth/ForgotPassword";
import EmailVerification from "./components/Auth/EmailVerification";
import ResetPassword from "./components/Auth/ResetPassword"; // <-- import it

function App() {
  return (
    <Router>
      <Routes>
        {/* Redirect root "/" to /signup */}
        <Route path="/" element={<Navigate to="/signup" replace />} />

        {/* Authentication Routes */}
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/verify-email" element={<EmailVerification />} />
        <Route path="/reset-password/:token" element={<ResetPassword />} /> {/* <-- Add this */}

        {/* Example protected route after login */}
        <Route path="/dashboard" element={<div>Welcome to Dashboard!</div>} />
      </Routes>
    </Router>
  );
}

export default App;
