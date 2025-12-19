import { Outlet, Link, useLocation } from 'react-router-dom';
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
  ChevronsRight,
  KeyRound
} from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import ChangePasswordModal from './ChangePasswordModal';

export default function Layout() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
  const userMenuRef = useRef(null);

  const navigation = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: ['admin', 'gestor', 'visualizador'] },
    { name: 'Categorias', path: '/categorias', icon: FolderOpen, roles: ['admin'] },
    { name: 'Lançamentos', path: '/lancamentos', icon: FileText, roles: ['admin', 'gestor'] },
    { name: 'Submissões', path: '/submissoes', icon: FileText, roles: ['gestor'] },
    { name: 'Reprovações', path: '/rejeicoes', icon: FileText, roles: ['admin'] },
    { name: 'Relatórios', path: '/relatorios', icon: BarChart3, roles: ['admin', 'gestor', 'visualizador'] },
    { name: 'Usuários', path: '/usuarios', icon: Users, roles: ['admin'] },
    { name: 'Logs', path: '/logs', icon: FileSearch, roles: ['admin'] },
  ];

  const filteredNavigation = navigation.filter(item => item.roles.includes(user?.papel));

  const handleLogout = () => {
    if (window.confirm('Deseja realmente sair?')) {
      logout();
    }
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className={`bg-white border-b border-gray-200 fixed w-full z-30 top-0 transition-all duration-300 ${isCollapsed ? 'lg:pl-20' : 'lg:pl-64'}`}>
        <div className="px-3 py-3 lg:px-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center justify-start">
              <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden p-2 text-gray-600 rounded-lg hover:bg-gray-100">
                {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
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

            <div className="relative" ref={userMenuRef}>
              <button onClick={() => setUserMenuOpen(!userMenuOpen)} className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100">
                <div className="text-right hidden md:block">
                  <p className="text-sm font-medium text-gray-900">{user?.nome}</p>
                  <p className="text-xs text-gray-500 capitalize">{user?.papel}</p>
                </div>
                <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
                  {user?.nome?.charAt(0).toUpperCase()}
                </div>
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                  <button
                    onClick={() => {
                      setShowChangePasswordModal(true);
                      setUserMenuOpen(false);
                    }}
                    className="w-full text-left flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <KeyRound size={16} className="mr-2" />
                    Alterar Senha
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <LogOut size={16} className="mr-2" />
                    Sair
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <aside className={`fixed top-0 left-0 z-40 h-screen pt-20 transition-transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} bg-white border-r border-gray-200 lg:translate-x-0 ${isCollapsed ? 'w-20' : 'w-64'} transition-width duration-300`}>
        <div className="h-full flex flex-col px-3 pb-4 overflow-y-auto overflow-x-hidden bg-white">
          <div className="flex items-center justify-between pt-1 mb-5">
            <button onClick={() => setIsCollapsed(!isCollapsed)} className={`hidden lg:block p-2 text-gray-500 rounded-lg hover:bg-gray-100 transition ${isCollapsed ? 'absolute top-[85px] left-1/2 -translate-x-1/2' : ''}`}>
              {isCollapsed ? <ChevronsRight size={20} /> : <ChevronsLeft size={20} />}
            </button>
          </div>
          <ul className="space-y-2 font-medium flex-grow">
            {filteredNavigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <li key={item.path} className="relative group">
                  <Link to={item.path} onClick={() => setSidebarOpen(false)} className={`flex items-center p-2 rounded-lg transition-all duration-200 ${isActive ? 'bg-indigo-50 text-indigo-600' : 'text-gray-900 hover:bg-gray-100'} ${isCollapsed ? 'justify-center' : ''}`}>
                    <Icon size={20} className={isActive ? 'text-indigo-600' : 'text-gray-500'} />
                    <span className={`ml-3 transition-all duration-200 whitespace-nowrap ${isCollapsed ? 'opacity-0 w-0 ml-0' : 'opacity-100'}`}>{item.name}</span>
                    {isCollapsed && <span className="absolute left-full ml-2 w-max px-2 py-1 text-sm text-white bg-gray-800 rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">{item.name}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </aside>

      {sidebarOpen && <div className="fixed inset-0 z-30 bg-gray-900/50 lg:hidden" onClick={() => setSidebarOpen(false)}></div>}

      <div className={`pt-20 transition-all duration-300 ${isCollapsed ? 'lg:ml-20' : 'lg:ml-64'}`}>
        <main className="p-4 md:p-6">
          <Outlet />
        </main>
      </div>

      {showChangePasswordModal && (
        <ChangePasswordModal onClose={() => setShowChangePasswordModal(false)} />
      )}
    </div>
  );
}