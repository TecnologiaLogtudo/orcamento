import { useState, useEffect } from 'react';
import { logsAPI } from '../services/api';
import { ChevronDown, ChevronUp } from 'lucide-react';

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({});
  const [page, setPage] = useState(1);
  const [expandedLog, setExpandedLog] = useState(null);

  useEffect(() => {
    loadLogs();
  }, [page]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await logsAPI.list({ page, per_page: 20 });
      setLogs(data.logs);
      setPagination(data.pagination);
    } catch (error) {
      alert('Erro ao carregar logs');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString('pt-BR');
  };

  const getDetalhesFormatados = (log) => {
    const detalhes = log.detalhes || {};
    const acao = log.acao || '';

    // Submissões
    if (acao.includes('Submissão em lote')) {
      const orcamentos = detalhes.orcamentos_submetidos || [];
      return {
        tipo: 'Submissão',
        titulo: `${detalhes.total_submetidos} orçamentos enviados para aprovação`,
        items: orcamentos.map(o => ({
          id: o.id_orcamento,
          categoria: o.categoria_nome,
          master: o.master,
          uf: o.uf,
          mes: o.mes,
          ano: o.ano,
        }))
      };
    }

    // Reprovações
    if (acao.includes('Reprovação em lote')) {
      const orcamentos = detalhes.orcamentos_reprovados || [];
      return {
        tipo: 'Reprovação',
        titulo: `${detalhes.total_reprovados} orçamentos rejeitados`,
        motivo: detalhes.motivo,
        items: orcamentos.map(o => ({
          id: o.id_orcamento,
          categoria: o.categoria_nome,
          master: o.master,
          uf: o.uf,
          mes: o.mes,
          ano: o.ano,
        }))
      };
    }

    return null;
  };

  const renderDetalhes = (log) => {
    const detalhes = getDetalhesFormatados(log);
    if (!detalhes) return null;

    const cor = detalhes.tipo === 'Submissão' ? 'indigo' : 'red';

    return (
      <div className={`bg-${cor}-50 border border-${cor}-200 rounded-lg p-4`}>
        <div className={`text-${cor}-900 font-semibold mb-3`}>
          {detalhes.tipo}: {detalhes.titulo}
        </div>

        {detalhes.motivo && (
          <div className={`text-${cor}-800 text-sm mb-3`}>
            <span className="font-medium">Motivo: </span>{detalhes.motivo}
          </div>
        )}

        <div className="space-y-2 max-h-64 overflow-y-auto">
          {detalhes.items.map((item, idx) => (
            <div key={idx} className={`text-${cor}-700 text-sm bg-white p-2 rounded border border-${cor}-200`}>
              <div className="font-medium">
                ID {item.id} - {item.categoria}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                Master: {item.master} | UF: {item.uf} | Período: {item.mes}/{item.ano}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900">Logs de Auditoria</h1>
        <p className="text-gray-600 mt-1">Histórico completo de ações no sistema</p>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase w-12"></th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Usuário</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ação</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tabela</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data/Hora</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {logs.map(log => (
                    <>
                      <tr 
                        key={log.id_log} 
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => setExpandedLog(expandedLog === log.id_log ? null : log.id_log)}
                      >
                        <td className="px-6 py-4 text-sm">
                          {getDetalhesFormatados(log) && (
                            expandedLog === log.id_log ? 
                              <ChevronUp size={18} /> : 
                              <ChevronDown size={18} />
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm">{log.usuario_nome || 'Sistema'}</td>
                        <td className="px-6 py-4 text-sm font-medium">{log.acao}</td>
                        <td className="px-6 py-4 text-sm">{log.tabela_afetada || '-'}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{formatDate(log.timestamp)}</td>
                      </tr>
                      {expandedLog === log.id_log && getDetalhesFormatados(log) && (
                        <tr>
                          <td colSpan="5" className="px-6 py-4">
                            {renderDetalhes(log)}
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            </div>

            {pagination.pages > 1 && (
              <div className="px-6 py-4 border-t flex justify-between items-center">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={!pagination.has_prev}
                  className="px-4 py-2 border rounded-lg disabled:opacity-50"
                >
                  Anterior
                </button>
                <span className="text-sm text-gray-600">
                  Página {pagination.page} de {pagination.pages}
                </span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={!pagination.has_next}
                  className="px-4 py-2 border rounded-lg disabled:opacity-50"
                >
                  Próxima
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}