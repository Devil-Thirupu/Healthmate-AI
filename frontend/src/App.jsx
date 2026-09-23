import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import MedicalRecordsPage from './pages/MedicalRecordsPage';
import ReportsPage from './pages/ReportsPage';
import PrescriptionsPage from './pages/PrescriptionsPage';
import AIAssistantPage from './pages/AIAssistantPage';
import AppointmentPreparationPage from './pages/AppointmentPreparationPage';
import NutritionPage from './pages/NutritionPage';
import SharingPage from './pages/SharingPage';
import AuditPage from './pages/AuditPage';
import SettingsPage from './pages/SettingsPage';
import PublicShareViewPage from './pages/PublicShareViewPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/share/:token" element={<PublicShareViewPage />} />
          <Route path="/shared/:token" element={<PublicShareViewPage />} />

          {/* Protected Clinical Vault Routes */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/records" element={<MedicalRecordsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/prescriptions" element={<PrescriptionsPage />} />
            <Route path="/ai-assistant" element={<AIAssistantPage />} />
            <Route path="/appointment-prep" element={<AppointmentPreparationPage />} />
            <Route path="/nutrition" element={<NutritionPage />} />
            <Route path="/sharing" element={<SharingPage />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
