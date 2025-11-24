import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import RejectionsLog from './RejectionsLog';

export default function Rejeicoes() {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();

  if (!isAdmin()) {
    return (
      <div className="text-center py-16">
        <h2 className="text-2xl font-bold text-gray-900">Acesso negado</h2>
        <p className="text-gray-600 mt-2">Apenas administradores podem acessar esta página.</p>
      </div>
    );
  }

  const handleNavigateToLancamentos = (filters) => {
    // Armazenar filtros em sessionStorage temporariamente
    sessionStorage.setItem('lancamentosFilters', JSON.stringify(filters));
    // Navegar para Lançamentos
    navigate('/lancamentos');
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Reprovações de Orçamentos</h1>
        <p className="text-gray-600 mt-2">
          Acompanhe os orçamentos rejeitados pelo gestor e clique para visualizá-los em Lançamentos e reenviar.
        </p>
      </div>

      <RejectionsLog onNavigateToLancamentos={handleNavigateToLancamentos} />
    </div>
  );
}
