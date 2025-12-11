
/*
import Signup from "./components/Auth/Signup";

function App() {
  return <Signup />;
}

export default App;
*/

import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import ToastProvider from "./components/Common/ToastProvider";
import Signup from "./components/Auth/Signup";
import Login from "./components/Auth/Login";
import ForgotPassword from "./components/Auth/ForgotPassword";
import EmailVerification from "./components/Auth/EmailVerification";
import ResetPassword from "./components/Auth/ResetPassword";
import VerifyEmailSuccess from "./components/Auth/VerifyEmailSuccess";
import Dashboard from "./components/Dashboard/Dashboard";
import FindSuppliers from "./components/TradeDirectory/FindSuppliers";
import FindBuyers from "./components/TradeDirectory/FindBuyers";
import CompanyProfile from "./components/TradeDirectory/CompanyProfile";
import Subscription from "./components/Subscriptions/Subscription";
import TradeLedger from "./components/TradeIntelligence/TradeLedger";
import TradePulse from "./components/TradeIntelligence/TradePulse";
import TradeLens from "./components/TradeIntelligence/TradeLens";
import LinkPrediction from "./components/TradeIntelligence/LinkPrediction";
import CompanyOverview from "./components/TradeIntelligence/CompanyOverview";
import CompanyProducts from "./components/TradeIntelligence/CompanyProducts";
import CompanyPartners from "./components/TradeIntelligence/CompanyPartners";
import CompanyTrends from "./components/TradeIntelligence/CompanyTrends";
import Watchlist from "./components/Watchlist/Watchlist";

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Public Route Component (redirect to dashboard if already logged in)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <Router>
            <Routes>
              {/* Public Routes */}
              <Route
              path="/"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            <Route
              path="/signup"
              element={
                <PublicRoute>
                  <Signup />
                </PublicRoute>
              }
            />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/email-verification" element={<EmailVerification />} />
            <Route path="/reset-password/:token" element={<ResetPassword />} />
            <Route path="/verify-email/:token" element={<VerifyEmailSuccess />} />

            {/* Protected Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            
            {/* Trade Directory Routes */}
            <Route
              path="/trade-directory/find-suppliers"
              element={
                <ProtectedRoute>
                  <FindSuppliers />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trade-directory/find-buyers"
              element={
                <ProtectedRoute>
                  <FindBuyers />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trade-directory/company/:id"
              element={
                <ProtectedRoute>
                  <CompanyProfile />
                </ProtectedRoute>
              }
            />
            
            {/* Watchlist Route */}
            <Route
              path="/watchlist"
              element={
                <ProtectedRoute>
                  <Watchlist />
                </ProtectedRoute>
              }
            />

            {/* Trade Intelligence Routes */}
            <Route
              path="/trade-intelligence/ledger"
              element={
                <ProtectedRoute>
                  <TradeLedger />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trade-intelligence/pulse"
              element={
                <ProtectedRoute>
                  <TradePulse />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trade-intelligence/lens"
              element={
                <ProtectedRoute>
                  <TradeLens />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trade-intelligence/link-prediction"
              element={
                <ProtectedRoute>
                  <LinkPrediction />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trade-intelligence/company/:id/overview"
              element={
                <ProtectedRoute>
                  <CompanyOverview />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trade-intelligence/company/:id/products"
              element={
                <ProtectedRoute>
                  <CompanyProducts />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trade-intelligence/company/:id/partners"
              element={
                <ProtectedRoute>
                  <CompanyPartners />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trade-intelligence/company/:id/trends"
              element={
                <ProtectedRoute>
                  <CompanyTrends />
                </ProtectedRoute>
              }
            />
            
            {/* Subscription Route */}
            <Route
              path="/subscription"
              element={
                <ProtectedRoute>
                  <Subscription />
                </ProtectedRoute>
              }
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ToastProvider>
  </ThemeProvider>
  );
}

export default App;
