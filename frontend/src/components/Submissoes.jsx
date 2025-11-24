import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SubmissionsLog from './SubmissionsLog';

export default function Submissoes() {
  const navigate = useNavigate();
  const { canApprove } = useAuth();

  if (!canApprove()) {
    return (
      <div className="text-center py-16">
        <h2 className="text-2xl font-bold text-gray-900">Acesso negado</h2>
        <p className="text-gray-600 mt-2">Apenas gestores podem acessar esta página.</p>
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
        <h1 className="text-3xl font-bold text-gray-900">Submissões para Aprovação</h1>
        <p className="text-gray-600 mt-2">
          Acompanhe os orçamentos submetidos pelo administrador e clique para visualizá-los em Lançamentos.
        </p>
      </div>

      <SubmissionsLog onNavigateToLancamentos={handleNavigateToLancamentos} />
    </div>
  );
}
