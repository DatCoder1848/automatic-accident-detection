import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Cameras from './pages/Cameras';
import Accidents from './pages/Accidents';
import AccidentDetail from './pages/AccidentDetail';
import Alerts from './pages/Alerts';
import { useSocket } from './hooks/useSocket';

function AppRoutes() {
  useSocket(); // Connect WebSocket and handle real-time events

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/cameras" element={<Cameras />} />
          <Route path="/accidents" element={<Accidents />} />
          <Route path="/accidents/:id" element={<AccidentDetail />} />
          <Route path="/alerts" element={<Alerts />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
