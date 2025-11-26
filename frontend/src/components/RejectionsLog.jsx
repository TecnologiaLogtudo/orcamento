import { useState, useEffect } from 'react';
import { orcamentosAPI } from '../services/api';
import { ArrowRight, Loader2, AlertCircle } from 'lucide-react';

export default function RejectionsLog({ onNavigateToLancamentos }) {
  const [rejections, setRejections] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRejections();
  }, []);

  const loadRejections = async () => {
    setLoading(true);
    try {
      const data = await orcamentosAPI.getRejections();
      setRejections(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Erro ao carregar reprovações:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = (rejection) => {
    const filters = {
      status: 'reprovado',
      ano: '',
    };
    if (onNavigateToLancamentos) {
      onNavigateToLancamentos(filters);
    }
  };

  const formatDate = (isoDate) => {
    if (!isoDate) return '-';
    return new Intl.DateTimeFormat('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(isoDate));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b">
        <h2 className="text-lg font-semibold text-gray-900">Log de Reprovações</h2>
        <p className="text-sm text-gray-600 mt-1">
          Histórico de orçamentos rejeitados pelo gestor para ajustes
        </p>
      </div>

      {rejections.length === 0 ? (
        <div className="text-center py-12">
          <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma reprovação encontrada</h3>
          <p className="mt-1 text-sm text-gray-500">Todos os orçamentos enviados estão sendo aprovados</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Gestor</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Centros de Custo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">UFs</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Categorias</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Motivo</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Ação</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rejections.map((rejection, idx) => (
                <tr key={idx} className="hover:bg-red-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDate(rejection.data)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {rejection.gestor_usuario}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center font-semibold text-red-600">
                    {rejection.total_reprovados}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {rejection.masters.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {rejection.masters.map((master, i) => (
                          <span
                            key={i}
                            className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                          >
                            {master}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {rejection.ufs.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {rejection.ufs.map((uf, i) => (
                          <span
                            key={i}
                            className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded"
                          >
                            {uf}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {rejection.categorias.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {rejection.categorias.slice(0, 2).map((cat, i) => (
                          <span
                            key={i}
                            className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded"
                          >
                            {cat}
                          </span>
                        ))}
                        {rejection.categorias.length > 2 && (
                          <span className="inline-block bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">
                            +{rejection.categorias.length - 2}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700 max-w-xs">
                    <div className="truncate" title={rejection.motivo}>
                      {rejection.motivo}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <button
                      onClick={() => handleNavigate(rejection)}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 hover:bg-red-200 rounded-md text-sm font-medium"
                      title="Ir para Lançamentos com filtros aplicados"
                    >
                      <ArrowRight size={16} />
                      Ver
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
