import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { useAuth } from "./lib/auth";
import { AuditLogsPage } from "./pages/AuditLogs";
import { ClientsPage } from "./pages/Clients";
import { DevicesPage } from "./pages/Devices";
import { KnowledgeBasePage } from "./pages/KnowledgeBase";
import { LoginPage } from "./pages/Login";
import { TicketDetailPage } from "./pages/TicketDetail";
import { TicketQueuePage } from "./pages/TicketQueue";
import { UsersPage } from "./pages/Users";

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
      <Route path="/tickets" element={<ProtectedLayout><TicketQueuePage /></ProtectedLayout>} />
      <Route path="/tickets/:ticketId" element={<ProtectedLayout><TicketDetailPage /></ProtectedLayout>} />
      <Route path="/devices" element={<ProtectedLayout><DevicesPage /></ProtectedLayout>} />
      <Route path="/users" element={<ProtectedLayout><UsersPage /></ProtectedLayout>} />
      <Route path="/clients" element={<ProtectedLayout><ClientsPage /></ProtectedLayout>} />
      <Route path="/knowledge-base" element={<ProtectedLayout><KnowledgeBasePage /></ProtectedLayout>} />
      <Route path="/audit-logs" element={<ProtectedLayout><AuditLogsPage /></ProtectedLayout>} />
      <Route path="*" element={<Navigate to="/tickets" replace />} />
    </Routes>
  );
}
