import { useState, useEffect, useMemo, useCallback } from 'react';
import { orcamentosAPI } from '../services/api';
import { categoriasAPI } from '../services/api';
import { Filter, RotateCcw, Save, Loader2, Send, Check, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Lancamentos() {
  const { user, canEdit, canApprove } = useAuth();
  const [orcamentos, setOrcamentos] = useState([]);
  const [originalOrcamentos, setOriginalOrcamentos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [modifiedIds, setModifiedIds] = useState(new Set());
  const [filtros, setFiltros] = useState({
    ano: new Date().getFullYear(),
    mes: new Date().getMonth() + 1,
    master: '',
    uf: '',
    categoria: ''
  });
  const [opcoesFiltro, setOpcoesFiltro] = useState({
    anos: [],
    masters: [],
    ufs: [],
    categorias: [],
    classes: [],
    meses: [
      { valor: 1, nome: 'Janeiro' }, { valor: 2, nome: 'Fevereiro' }, { valor: 3, nome: 'Março' },
      { valor: 4, nome: 'Abril' }, { valor: 5, nome: 'Maio' }, { valor: 6, nome: 'Junho' },
      { valor: 7, nome: 'Julho' }, { valor: 8, nome: 'Agosto' }, { valor: 9, nome: 'Setembro' },
      { valor: 10, nome: 'Outubro' }, { valor: 11, nome: 'Novembro' }, { valor: 12, nome: 'Dezembro' }
    ]
  });

  useEffect(() => {
    loadFiltrosDisponiveis();
  }, []);

  useEffect(() => {
    loadOrcamentos();
  }, [filtros.ano, filtros.mes, filtros.master, filtros.uf, filtros.categoria]);

  const loadFiltrosDisponiveis = useCallback(async () => {
    try {
      const data = await orcamentosAPI.getFiltros();
      
      // O endpoint de filtros já retorna uma lista distinta de nomes de categorias.
      // Vamos garantir que o estado `opcoesFiltro.categorias` seja uma lista de strings.
      // A busca extra por `categoriasAPI.list()` foi removida para simplificar e usar a fonte correta.
      setOpcoesFiltro(prev => ({
        ...prev,
        ...data,
        // Garante que `categorias` seja sempre um array de strings.
        categorias: data.categorias || []
      }));
      // Inicializa o filtro de ano com o mais recente, se disponível
      if (data.anos && data.anos.length > 0) {
        setFiltros(prev => ({ ...prev, ano: data.anos[0] }));
      }
    } catch (error) {
      console.error('Erro ao carregar filtros:', error);
    }
  }, []);
  

  const loadOrcamentos = useCallback(async () => {
    setLoading(true);
    try {      
      // 1. Buscar todas as categorias que correspondem aos filtros (master, uf, categoria)
      const categoriasResponse = await categoriasAPI.list({
        master: filtros.master,
        uf: filtros.uf,
        categoria: filtros.categoria
      });
      const todasCategorias = Array.isArray(categoriasResponse) ? categoriasResponse : [];

      // 2. Buscar os orçamentos existentes para o ano/mês selecionado
      const orcamentosResponse = await orcamentosAPI.list({
        ano: filtros.ano,
        mes: filtros.mes,
        master: filtros.master,
        uf: filtros.uf,
        categoria: filtros.categoria
      });
      const orcamentosExistentes = Array.isArray(orcamentosResponse) ? orcamentosResponse : [];
      const orcamentosMap = new Map(orcamentosExistentes.map(o => [o.id_categoria, o]));

      // 3. Mesclar as duas listas
      const orcamentosCompletos = todasCategorias.map(cat => {
        const orcamentoExistente = orcamentosMap.get(cat.id_categoria);
        return orcamentoExistente || {
          id_categoria: cat.id_categoria,
          categoria: cat,
          mes: filtros.mes,
          ano: filtros.ano,
          orcado: 0,
          realizado: 0,
          dif: 0,
          status: 'rascunho'
        };
      });

      setOrcamentos(orcamentosCompletos);
      setOriginalOrcamentos(JSON.parse(JSON.stringify(orcamentosCompletos)));
      setModifiedIds(new Set());
    } catch (error) {
      console.error('Erro ao carregar orçamentos:', error);
    } finally {
      setLoading(false);
    }
  }, [filtros]); // Dependência do objeto de filtros completo

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({
      ...prev,
      [name]: (name === 'ano' || name === 'mes') ? (value === '' ? '' : parseInt(value, 10)) : value
    }));
  };

  const handleLimparFiltros = () => {
    const currentYear = new Date().getFullYear();
    setFiltros({
      mes: new Date().getMonth() + 1,
      ano: opcoesFiltro.anos?.includes(currentYear) ? currentYear : (opcoesFiltro.anos?.[0] || currentYear),
      master: '',
      uf: '',
      categoria: ''
    });
  };

  const handleValueChange = (orcamento, field, value) => {
    const uniqueId = orcamento.id_orcamento || `${orcamento.id_categoria}-${orcamento.mes}-${orcamento.ano}`;

    setOrcamentos(prev =>
      prev.map(orc => {
        const currentId = orc.id_orcamento || `${orc.id_categoria}-${orc.mes}-${orc.ano}`;
        if (currentId !== uniqueId) return orc;

        const newValue = parseFloat(value) || 0;
        const updatedOrc = { ...orc, [field]: newValue };

        // Recalcular diferença
        const orcado = updatedOrc.orcado || 0;
        const realizado = updatedOrc.realizado || 0;
        updatedOrc.dif = orcado - realizado;

        setModifiedIds(prevIds => new Set(prevIds).add(uniqueId));
        return updatedOrc;
      })
    );
  };

  const handleSendForApproval = async () => {
    const modifiedOrcamentos = orcamentos.filter(orc => {
      const uniqueId = orc.id_orcamento || `${orc.id_categoria}-${orc.mes}-${orc.ano}`;
      // Apenas rascunhos modificados
      return modifiedIds.has(uniqueId) && orc.status === 'rascunho';
    });

    if (modifiedOrcamentos.length === 0) {
      alert('Nenhum rascunho modificado para enviar.');
      return;
    }

    setSaving(true);
    try {
      // Passo 1: Salvar as alterações
      const orcamentosPayload = modifiedOrcamentos.map(orc => {
        const { categoria, ...rest } = orc;
        const mesObj = opcoesFiltro.meses.find(m => m.valor === rest.mes);
        return {
          ...rest,
          mes: mesObj ? mesObj.nome : rest.mes,
          id_orcamento: rest.id_orcamento || null
        };
      });

      const savedResult = await orcamentosAPI.batchUpdate(orcamentosPayload);
      
      // Passo 2: Submeter os orçamentos salvos/atualizados para aprovação
      // O backend retorna os IDs dos orçamentos criados/atualizados
      const idsToSubmit = savedResult.orcamentos.map(o => o.id_orcamento);
      if (idsToSubmit.length > 0) {
        await orcamentosAPI.batchSubmit(idsToSubmit);
      }

      alert(`${modifiedOrcamentos.length} orçamento(s) enviado(s) para aprovação com sucesso!`);
      loadOrcamentos();
    } catch (error) {
      alert('Erro ao enviar para aprovação: ' + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (orcamentoId, newStatus) => {
    try {
      let apiCall;
      switch (newStatus) {
        case 'aprovado':
          // Assumindo que a API tem um endpoint para aprovar
          apiCall = orcamentosAPI.aprovar(orcamentoId);
          break;
        case 'rascunho': // Reprovar volta para rascunho
          // Assumindo que a API tem um endpoint para reprovar
          apiCall = orcamentosAPI.reprovar(orcamentoId);
          break;
        default:
          // A submissão agora é em lote, então o caso 'aguardando_aprovacao' individual foi removido.
          throw new Error('Ação de status desconhecida.');
      }
      await apiCall;
      alert(`Orçamento atualizado com sucesso!`);
      loadOrcamentos(); // Recarrega para refletir a mudança de status
    } catch (error) {
      alert('Erro ao atualizar status: ' + (error.response?.data?.error || error.message));
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0);
  };

  const getStatusBadge = (status) => {
    const badges = {
      rascunho: 'bg-gray-100 text-gray-800',
      aguardando_aprovacao: 'bg-yellow-100 text-yellow-800',
      aprovado: 'bg-green-100 text-green-800',
      reprovado: 'bg-red-100 text-red-800'
    };
    return badges[status] || badges.rascunho;
  };

  const resumo = useMemo(() => {
    return orcamentos.reduce((acc, orc) => {
      return {
        totalOrcado: acc.totalOrcado + (orc.orcado || 0),
        totalRealizado: acc.totalRealizado + (orc.realizado || 0),
      };
    }, { totalOrcado: 0, totalRealizado: 0 });
  }, [orcamentos]);

  return (
    <div className="space-y-6">
      {/* Header e Filtros */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <h1 className="text-2xl font-bold text-gray-900">Lançamentos</h1>
          <button
            onClick={handleLimparFiltros}
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <RotateCcw size={16} />
            Limpar Filtros
          </button>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-5 gap-4">
          <select name="ano" value={filtros.ano} onChange={handleFiltroChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
            {(opcoesFiltro.anos && opcoesFiltro.anos.length > 0)
              ? opcoesFiltro.anos.map(y => <option key={`ano-${y}`} value={y}>{y}</option>)
              : <option value={filtros.ano}>{filtros.ano}</option>
            }
          </select>
          <select name="mes" value={filtros.mes} onChange={handleFiltroChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
            <option value="">Todos os Meses</option>
            {opcoesFiltro.meses.map(m => <option key={`mes-${m.valor}`} value={m.valor}>{m.nome}</option>)}
          </select>
          <select name="categoria" value={filtros.categoria} onChange={handleFiltroChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
            <option value="">Todas as Categorias</option>            
            {opcoesFiltro.categorias?.map((cat) => (
              <option key={`cat-${cat}`} value={cat}>{cat}</option>
            ))}
          </select>
          <select name="master" value={filtros.master} onChange={handleFiltroChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
            <option value="">Todos os Centros de Custo</option>
            {opcoesFiltro.masters?.map(m => <option key={`master-${m}`} value={m}>{m}</option>)}
          </select>
          <select name="uf" value={filtros.uf} onChange={handleFiltroChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
            <option value="">Todas as UFs</option>
            {opcoesFiltro.ufs?.map(u => <option key={`uf-${u}`} value={u}>{u}</option>)}
          </select>
        </div>

        {canEdit() && modifiedIds.size > 0 && orcamentos.some(o => modifiedIds.has(o.id_orcamento || `${o.id_categoria}-${o.mes}-${o.ano}`) && o.status === 'rascunho') && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleSendForApproval}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <Send size={20} />
              )}
              Enviar Rascunhos para Aprovação
            </button>
          </div>
        )}
      </div>

      {/* Tabela de Lançamentos */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
    {loading ? (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    ) : orcamentos.length > 0 ? (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">C. Custo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grupo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">UF</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Orçado</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Realizado</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Diferença</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Ações</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {orcamentos.map((orc) => (
              <tr key={orc.id_orcamento || `${orc.id_categoria}-${orc.mes}-${orc.ano}`} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{orc.categoria?.master || ''}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{orc.categoria?.grupo || ''}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{orc.categoria?.uf || ''}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                  {/* Regra de edição: pode editar se tiver permissão E o status não for 'aprovado' */}
                  {canEdit() && orc.status !== 'aprovado' ? (
                    <input
                      type="number"
                      value={orc.orcado || ''}
                      onChange={(e) => handleValueChange(orc, 'orcado', e.target.value)}
                      className="w-32 px-2 py-1 border rounded-md text-right focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  ) : (
                    formatCurrency(orc.orcado)
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                  {canEdit() && orc.status !== 'aprovado' ? (
                    <input
                      type="number"
                      value={orc.realizado || ''}
                      onChange={(e) => handleValueChange(orc, 'realizado', e.target.value)}
                      className="w-32 px-2 py-1 border rounded-md text-right focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  ) : (
                    formatCurrency(orc.realizado)
                  )}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-semibold ${orc.dif >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(orc.dif)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(orc.status)}`}>
                    {(orc.status || '').replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                  <div className="flex items-center justify-center gap-2">
                    {/* Ações do Gestor */}
                    {canApprove() && orc.status === 'aguardando_aprovacao' && (
                      <>
                        <button onClick={() => handleStatusChange(orc.id_orcamento, 'aprovado')} className="text-green-600 hover:text-green-900" title="Aprovar">
                          <Check size={18} />
                        </button>
                        <button onClick={() => handleStatusChange(orc.id_orcamento, 'rascunho')} className="text-red-600 hover:text-red-900" title="Reprovar">
                          <X size={18} />
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Resumo */}
        <div className="bg-gray-50 px-6 py-4 border-t">
          <h3 className="text-lg font-semibold mb-2">Resumo dos Lançamentos Filtrados</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-800 font-medium">Total Orçado</p>
              <p className="text-xl font-bold text-blue-900">{formatCurrency(resumo.totalOrcado)}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-green-800 font-medium">Total Realizado</p>
              <p className="text-xl font-bold text-green-900">{formatCurrency(resumo.totalRealizado)}</p>
            </div>
            <div className={`p-4 rounded-lg ${(resumo.totalOrcado - resumo.totalRealizado) >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
              <p className={`text-sm font-medium ${(resumo.totalOrcado - resumo.totalRealizado) >= 0 ? 'text-green-800' : 'text-red-800'}`}>Diferença Total</p>
              <p className={`text-xl font-bold ${(resumo.totalOrcado - resumo.totalRealizado) >= 0 ? 'text-green-900' : 'text-red-900'}`}>{formatCurrency(resumo.totalOrcado - resumo.totalRealizado)}</p>
            </div>
          </div>
        </div>
      </div>
    ) : (
      <div className="text-center py-16">
        <Filter className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum lançamento encontrado</h3>
        <p className="mt-1 text-sm text-gray-500">Ajuste os filtros para encontrar resultados.</p>
      </div>
    )}
  </div>
    </div >
  );
}