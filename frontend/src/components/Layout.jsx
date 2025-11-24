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
  X,
  ChevronsLeft,
  ChevronsRight
} from 'lucide-react';
import { useState } from 'react';

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAdmin, canEdit } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

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
      name: 'Submissões', 
      path: '/submissoes', 
      icon: FileText, 
      roles: ['gestor'] 
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
      {/* Navbar - Agora com padding que se ajusta à sidebar */}
      <nav className={`bg-white border-b border-gray-200 fixed w-full z-30 top-0 transition-all duration-300 ${
        isCollapsed ? 'lg:pl-20' : 'lg:pl-64'
      }`}>
        <div className="px-3 py-3 lg:px-5">
          <div className="flex items-center justify-between ">
            <div className="flex items-center justify-start">
              {/* Mobile menu button */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 text-gray-600 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200"
              >
                {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
              </button>

              {/* Logo - Oculto em telas grandes para não sobrepor */}
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
        className={`fixed top-0 left-0 z-40 h-screen pt-20 transition-transform ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } bg-white border-r border-gray-200 lg:translate-x-0 ${
          isCollapsed ? 'w-20' : 'w-64'
        } transition-width duration-300`}
      >
        <div className="h-full flex flex-col px-3 pb-4 overflow-y-auto overflow-x-hidden bg-white">
          {/* Logo e botão de recolher/expandir */}
          <div className="flex items-center justify-between pt-1 mb-5">
            {/* Logo - some quando recolhido */}
            <Link to="/dashboard" className={`flex items-center transition-opacity duration-200 ${isCollapsed ? 'opacity-0 pointer-events-none w-0' : 'opacity-100'}`}>
              <div className="flex items-center justify-center w-10 h-10 bg-indigo-600 rounded-lg">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
              <span className="ml-3 text-xl font-semibold text-gray-900 whitespace-nowrap">
                Controle
              </span>
            </Link>
            
            {/* Botão de recolher/expandir */}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className={`hidden lg:block p-2 text-gray-500 rounded-lg hover:bg-gray-100 transition ${isCollapsed ? 'absolute top-[85px] left-1/2 -translate-x-1/2' : ''}`}
            >
              {isCollapsed ? <ChevronsRight size={20} /> : <ChevronsLeft size={20} />}
            </button>
          </div>

          <ul className="space-y-2 font-medium flex-grow">
            {filteredNavigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <li key={item.path} className="relative group">
                  <Link
                    to={item.path}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center p-2 rounded-lg transition-all duration-200 ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-600'
                        : 'text-gray-900 hover:bg-gray-100'
                    } ${isCollapsed ? 'justify-center' : ''}`}
                  >
                    <Icon size={20} className={isActive ? 'text-indigo-600' : 'text-gray-500'} />
                    <span className={`ml-3 transition-all duration-200 whitespace-nowrap ${isCollapsed ? 'opacity-0 w-0 ml-0' : 'opacity-100'}`}>{item.name}</span>
                    {isCollapsed && (
                      <span className="absolute left-full ml-2 w-max px-2 py-1 text-sm text-white bg-gray-800 rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                        {item.name}
                      </span>
                    )}
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
      <div className={`pt-20 transition-all duration-300 ${
        isCollapsed ? 'lg:ml-20' : 'lg:ml-64'
      }`}>
        <main className="p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}