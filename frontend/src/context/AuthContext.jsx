import { createContext, useContext, useState, useEffect } from 'react';
import api, { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    const savedToken = localStorage.getItem('token');

    if (savedUser && savedToken !== 'undefined' && savedToken) {
      try {
        setUser(JSON.parse(savedUser));
        api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`;
    } catch (err) {
        console.error('Erro ao analisar o usuário salvo:', err);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }

    setLoading(false);
  }, []);

  const login = async (email, senha) => {
    setLoading(true);
    try {
      const data = await authAPI.login(email, senha);

      const token = data.access_token;
      const usuario = data.usuario;

      // Salvar token e usuário no localStorage
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(usuario));

      // Configurar header global
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

      setUser(usuario);

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Erro ao fazer login',
      };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
    window.location.href = '/login';
  };

  const isAdmin = () => user?.papel === 'admin';
  const isGestor = () => user?.papel === 'gestor';
  const isVisualizador = () => user?.papel === 'visualizador';

  const canEdit = () => ['admin', 'gestor'].includes(user?.papel);
  const canApprove = () => user?.papel === 'gestor';

  const value = {
    user,
    loading,
    login,
    logout,
    isAdmin,
    isGestor,
    isVisualizador,
    canEdit,
    canApprove,
    isAuthenticated: !!user,
  };

  if (loading) {
    return <div className="loading">Carregando...</div>;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider');
  }
  return context;
};
