import { useState, useEffect } from 'react';
import { orcamentosAPI } from '../services/api';
import { ArrowRight, Calendar } from 'lucide-react';

export default function SubmissionsLog({ onNavigateToLancamentos }) {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSubmissions();
  }, []);

  const loadSubmissions = async () => {
    setLoading(true);
    try {
      const data = await orcamentosAPI.getSubmissions();
      setSubmissions(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Erro ao carregar submissões:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = (submission) => {
    if (onNavigateToLancamentos) {
      onNavigateToLancamentos(submission);
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b">
        <h2 className="text-lg font-semibold text-gray-900">Log de Submissões para Aprovação</h2>
        <p className="text-sm text-gray-600 mt-1">
          Histórico de orçamentos enviados pelo administrador para sua aprovação
        </p>
      </div>

      {submissions.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma submissão encontrada</h3>
          <p className="mt-1 text-sm text-gray-500">Aguardando envio de orçamentos para aprovação</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Admin</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Centros de Custo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">UFs</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Categorias</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Ação</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {submissions.map((submission, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDate(submission.data)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {submission.admin_usuario}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center font-semibold text-indigo-600">
                    {submission.total_submetidos}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {submission.masters.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {submission.masters.map((master, i) => (
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
                    {submission.ufs.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {submission.ufs.map((uf, i) => (
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
                    {submission.categorias.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {submission.categorias.slice(0, 2).map((cat, i) => (
                          <span
                            key={i}
                            className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded"
                          >
                            {cat}
                          </span>
                        ))}
                        {submission.categorias.length > 2 && (
                          <span className="inline-block bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">
                            +{submission.categorias.length - 2}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <button
                      onClick={() => handleNavigate(submission)}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-100 text-indigo-700 hover:bg-indigo-200 rounded-md text-sm font-medium"
                      title="Ver detalhes da submissão"
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
