import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  DollarSign, 
  LayoutDashboard, 
  FolderOpen, 
  FileText, 
  BarChart3, 
  Users, 
  FileSearch,
  LogOut,
  Menu,
  X
} from 'lucide-react';
import { useState } from 'react';

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAdmin, canEdit } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { 
      name: 'Dashboard', 
      path: '/dashboard', 
      icon: LayoutDashboard, 
      roles: ['admin', 'gestor', 'visualizador'] 
    },
    { 
      name: 'Categorias', 
      path: '/categorias', 
      icon: FolderOpen, 
      roles: ['admin'] 
    },
    { 
      name: 'Lançamentos', 
      path: '/lancamentos', 
      icon: FileText, 
      roles: ['admin', 'gestor'] 
    },
    { 
      name: 'Relatórios', 
      path: '/relatorios', 
      icon: BarChart3, 
      roles: ['admin', 'gestor', 'visualizador'] 
    },
    { 
      name: 'Usuários', 
      path: '/usuarios', 
      icon: Users, 
      roles: ['admin'] 
    },
    { 
      name: 'Logs', 
      path: '/logs', 
      icon: FileSearch, 
      roles: ['admin'] 
    },
  ];

  const filteredNavigation = navigation.filter(item => 
    item.roles.includes(user?.papel)
  );

  const handleLogout = () => {
    if (window.confirm('Deseja realmente sair?')) {
      logout();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 fixed w-full z-30 top-0">
        <div className="px-3 py-3 lg:px-5 lg:pl-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center justify-start">
              {/* Mobile menu button */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 text-gray-600 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200"
              >
                {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
              </button>

              {/* Logo */}
              <Link to="/dashboard" className="flex ml-2 md:mr-24">
                <div className="flex items-center">
                  <div className="flex items-center justify-center w-10 h-10 bg-indigo-600 rounded-lg">
                    <DollarSign className="w-6 h-6 text-white" />
                  </div>
                  <span className="ml-3 text-xl font-semibold text-gray-900">
                    Controle Orçamentário
                  </span>
                </div>
              </Link>
            </div>

            {/* User menu */}
            <div className="flex items-center">
              <div className="flex items-center ml-3">
                <div className="text-right mr-4 hidden md:block">
                  <p className="text-sm font-medium text-gray-900">{user?.nome}</p>
                  <p className="text-xs text-gray-500 capitalize">{user?.papel}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center p-2 text-gray-600 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200"
                  title="Sair"
                >
                  <LogOut size={20} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-40 w-64 h-screen pt-20 transition-transform ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } bg-white border-r border-gray-200 lg:translate-x-0`}
      >
        <div className="h-full px-3 pb-4 overflow-y-auto bg-white">
          <ul className="space-y-2 font-medium">
            {filteredNavigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center p-2 rounded-lg transition ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-600'
                        : 'text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <Icon size={20} className={isActive ? 'text-indigo-600' : 'text-gray-500'} />
                    <span className="ml-3">{item.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-gray-900/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}

      {/* Main content */}
      <div className="lg:ml-64 pt-20">
        <main className="p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}