import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { useAuth } from "./lib/auth";
import { DashboardPage } from "./pages/Dashboard";
import { DiagnosticsPage } from "./pages/Diagnostics";
import { LoginPage } from "./pages/Login";
import { MyDevicePage } from "./pages/MyDevice";
import { NewTicketPage } from "./pages/NewTicket";
import { SettingsPage } from "./pages/Settings";
import { TicketDetailPage } from "./pages/TicketDetail";

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="flex min-h-screen items-center justify-center bg-nova-bg text-nova-muted">Loading…</div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<ProtectedLayout><DashboardPage /></ProtectedLayout>} />
      <Route path="/new-ticket" element={<ProtectedLayout><NewTicketPage /></ProtectedLayout>} />
      <Route path="/tickets/:ticketId" element={<ProtectedLayout><TicketDetailPage /></ProtectedLayout>} />
      <Route path="/diagnostics" element={<ProtectedLayout><DiagnosticsPage /></ProtectedLayout>} />
      <Route path="/my-device" element={<ProtectedLayout><MyDevicePage /></ProtectedLayout>} />
      <Route path="/settings" element={<ProtectedLayout><SettingsPage /></ProtectedLayout>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
