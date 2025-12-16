import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Categorias from './components/Categorias';
import Lancamentos from './components/Lancamentos';
import Submissoes from './components/Submissoes';
import Rejeicoes from './components/Rejeicoes';
import Relatorios from './components/Relatorios';
import Usuarios from './components/Usuarios';
import Logs from './components/Logs';
import Layout from './components/Layout';

// Componente para proteger rotas
function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
}

// Componente para rotas restritas por papel
function RestrictedRoute({ children, allowedRoles }) {
  const { user, isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (!allowedRoles.includes(user?.papel)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">403</h1>
          <p className="text-gray-600 mb-8">
            Você não tem permissão para acessar esta página
          </p>
          <a
            href="/dashboard"
            className="inline-block bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition"
          >
            Voltar ao Dashboard
          </a>
        </div>
      </div>
    );
  }

  return children;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Rota pública */}
      <Route path="/login" element={<Login />} />

      {/* Rotas privadas */}
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" />} />
        
        <Route path="dashboard" element={<Dashboard />} />
        
        <Route path="categorias" element={
          <RestrictedRoute allowedRoles={['admin']}>
            <Categorias />
          </RestrictedRoute>
        } />
        
        <Route path="lancamentos" element={
          <RestrictedRoute allowedRoles={['admin', 'gestor']}>
            <Lancamentos />
          </RestrictedRoute>
        } />
        
        <Route path="submissoes" element={
          <RestrictedRoute allowedRoles={['gestor']}>
            <Submissoes />
          </RestrictedRoute>
        } />
        
        <Route path="rejeicoes" element={
          <RestrictedRoute allowedRoles={['admin']}>
            <Rejeicoes />
          </RestrictedRoute>
        } />
        
        <Route path="relatorios" element={<Relatorios />} />
        
        <Route path="usuarios" element={
          <RestrictedRoute allowedRoles={['admin']}>
            <Usuarios />
          </RestrictedRoute>
        } />
        
                <Route path="logs" element={
                  <RestrictedRoute allowedRoles={['admin']}>
                    <Logs />
                  </RestrictedRoute>
                } />
      </Route>

      {/* Rota 404 */}
      <Route
        path="*"
        element={
          <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
              <p className="text-gray-600 mb-8">Página não encontrada</p>
              <a
                href="/dashboard"
                className="inline-block bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition"
              >
                Voltar ao Dashboard
              </a>
            </div>
          </div>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;