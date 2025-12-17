


import React, { Suspense } from "react";
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
import Watchlist from "./components/Watchlist/Watchlist";


const TradeLedger = React.lazy(() => import("./components/TradeIntelligence/TradeLedger"));
const TradePulse = React.lazy(() => import("./components/TradeIntelligence/TradePulse"));
const TradeLens = React.lazy(() => import("./components/TradeIntelligence/TradeLens"));
const LinkPrediction = React.lazy(() => import("./components/TradeIntelligence/LinkPrediction"));
const CompanyOverview = React.lazy(() => import("./components/TradeIntelligence/CompanyOverview"));
const CompanyProducts = React.lazy(() => import("./components/TradeIntelligence/CompanyProducts"));
const CompanyPartners = React.lazy(() => import("./components/TradeIntelligence/CompanyPartners"));
const CompanyTrends = React.lazy(() => import("./components/TradeIntelligence/CompanyTrends"));
const CompareCompanies = React.lazy(() => import("./components/TradeIntelligence/CompareCompanies"));


const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
  </div>
);


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
            <Suspense fallback={<PageLoader />}>
              <Routes>
                {}
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

                {}
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                
                {}
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
                
                {}
                <Route
                  path="/watchlist"
                  element={
                    <ProtectedRoute>
                      <Watchlist />
                    </ProtectedRoute>
                  }
                />

                {}
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
                  path="/trade-intelligence/compare"
                  element={
                    <ProtectedRoute>
                      <CompareCompanies />
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
                
                {}
                <Route
                  path="/subscription"
                  element={
                    <ProtectedRoute>
                      <Subscription />
                    </ProtectedRoute>
                  }
                />

                {}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </Router>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
