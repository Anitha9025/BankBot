import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import PrivateRoute from "./components/PrivateRoute";
import Layout from "./components/Layout";

import LoginPage       from "./pages/LoginPage";
import DashboardPage   from "./pages/DashboardPage";
import UserQueriesPage from "./pages/UserQueriesPage";
import FAQsPage        from "./pages/FAQsPage";
import TrainingDataPage from "./pages/TrainingDataPage";
import AnalyticsPage   from "./pages/AnalyticsPage";

function AdminApp() {
  return (
    <Layout>
      <Routes>
        <Route path="/"          element={<DashboardPage />} />
        <Route path="/queries"   element={<UserQueriesPage />} />
        <Route path="/faqs"      element={<FAQsPage />} />
        <Route path="/training"  element={<TrainingDataPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="*"          element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/*"     element={<PrivateRoute><AdminApp /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
