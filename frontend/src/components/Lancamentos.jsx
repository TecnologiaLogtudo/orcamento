import { useState, useEffect } from 'react';
import { categoriasAPI, orcamentosAPI } from '../services/api';
import { Save, Check, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
              'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];

export default function Lancamentos() {
  const { canApprove } = useAuth();
  const [categorias, setCategorias] = useState([]);
  const [categoriaSelecionada, setCategoriaSelecionada] = useState(null);
  const [ano, setAno] = useState(new Date().getFullYear());
  const [orcamentos, setOrcamentos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadCategorias();
  }, []);

  useEffect(() => {
    if (categoriaSelecionada) {
      loadOrcamentos();
    }
  }, [categoriaSelecionada, ano]);

  const loadCategorias = async () => {
    try {
      const data = await categoriasAPI.list();
      setCategorias(data);
    } catch (error) {
      alert('Erro ao carregar categorias');
    }
  };

  const loadOrcamentos = async () => {
    if (!categoriaSelecionada) return;
    
    try {
      setLoading(true);
      const data = await orcamentosAPI.getCategoriaAno(categoriaSelecionada, ano);
      setOrcamentos(data.orcamentos || []);
    } catch (error) {
      alert('Erro ao carregar orçamentos');
    } finally {
      setLoading(false);
    }
  };

  const handleValueChange = (index, field, value) => {
    const newOrcamentos = [...orcamentos];
    newOrcamentos[index][field] = parseFloat(value) || 0;
    newOrcamentos[index].dif = newOrcamentos[index].realizado - newOrcamentos[index].orcado;
    setOrcamentos(newOrcamentos);
  };

  const handleSave = async () => {
    if (!categoriaSelecionada) {
      alert('Selecione uma categoria');
      return;
    }

    try {
      setSaving(true);
      const orcamentosParaSalvar = orcamentos.map(orc => ({
        id_categoria: categoriaSelecionada,
        mes: orc.mes,
        ano: ano,
        orcado: orc.orcado,
        realizado: orc.realizado,
        status: orc.status || 'rascunho'
      }));

      await orcamentosAPI.batchUpdate(orcamentosParaSalvar);
      alert('Orçamentos salvos com sucesso!');
      loadOrcamentos();
    } catch (error) {
      alert('Erro ao salvar: ' + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const handleAprovar = async (idOrcamento) => {
    if (!window.confirm('Deseja aprovar este orçamento?')) return;

    try {
      await orcamentosAPI.aprovar(idOrcamento);
      alert('Orçamento aprovado!');
      loadOrcamentos();
    } catch (error) {
      alert('Erro ao aprovar: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleReprovar = async (idOrcamento) => {
    const motivo = prompt('Motivo da reprovação:');
    if (!motivo) return;

    try {
      await orcamentosAPI.reprovar(idOrcamento, motivo);
      alert('Orçamento reprovado!');
      loadOrcamentos();
    } catch (error) {
      alert('Erro ao reprovar: ' + (error.response?.data?.error || error.message));
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const getStatusBadge = (status) => {
    const badges = {
      rascunho: 'bg-gray-100 text-gray-800',
      aguardando_aprovacao: 'bg-yellow-100 text-yellow-800',
      aprovado: 'bg-green-100 text-green-800'
    };
    return badges[status] || badges.rascunho;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Lançamentos Orçamentários</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Categoria
            </label>
            <select
              value={categoriaSelecionada || ''}
              onChange={(e) => setCategoriaSelecionada(parseInt(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Selecione uma categoria</option>
              {categorias.map(cat => (
                <option key={cat.id_categoria} value={cat.id_categoria}>
                  {cat.dono} - {cat.grupo || cat.tipo_despesa}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ano
            </label>
            <select
              value={ano}
              onChange={(e) => setAno(parseInt(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {[2023, 2024, 2025, 2026].map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Tabela de Lançamentos */}
      {categoriaSelecionada && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mês</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Orçado</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Realizado</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Diferença</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      {canApprove() && (
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Ações</th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {orcamentos.map((orc, index) => (
                      <tr key={orc.mes} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {orc.mes}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="number"
                            step="0.01"
                            value={orc.orcado}
                            onChange={(e) => handleValueChange(index, 'orcado', e.target.value)}
                            disabled={orc.status === 'aprovado'}
                            className="w-32 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-100"
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="number"
                            step="0.01"
                            value={orc.realizado}
                            onChange={(e) => handleValueChange(index, 'realizado', e.target.value)}
                            disabled={orc.status === 'aprovado'}
                            className="w-32 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-100"
                          />
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-semibold ${
                          orc.dif >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatCurrency(orc.dif)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(orc.status)}`}>
                            {orc.status === 'rascunho' ? 'Rascunho' :
                             orc.status === 'aguardando_aprovacao' ? 'Aguardando' :
                             'Aprovado'}
                          </span>
                        </td>
                        {canApprove() && orc.id_orcamento && (
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                            {orc.status !== 'aprovado' && (
                              <>
                                <button
                                  onClick={() => handleAprovar(orc.id_orcamento)}
                                  className="text-green-600 hover:text-green-900 mr-3"
                                  title="Aprovar"
                                >
                                  <Check size={18} />
                                </button>
                                <button
                                  onClick={() => handleReprovar(orc.id_orcamento)}
                                  className="text-red-600 hover:text-red-900"
                                  title="Reprovar"
                                >
                                  <X size={18} />
                                </button>
                              </>
                            )}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-gray-50">
                    <tr>
                      <td className="px-6 py-4 text-sm font-bold text-gray-900">TOTAL</td>
                      <td className="px-6 py-4 text-sm font-bold text-gray-900">
                        {formatCurrency(orcamentos.reduce((sum, o) => sum + o.orcado, 0))}
                      </td>
                      <td className="px-6 py-4 text-sm font-bold text-gray-900">
                        {formatCurrency(orcamentos.reduce((sum, o) => sum + o.realizado, 0))}
                      </td>
                      <td className={`px-6 py-4 text-sm font-bold ${
                        orcamentos.reduce((sum, o) => sum + o.dif, 0) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {formatCurrency(orcamentos.reduce((sum, o) => sum + o.dif, 0))}
                      </td>
                      <td colSpan={canApprove() ? 2 : 1}></td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              <div className="p-6 border-t border-gray-200">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                >
                  <Save size={20} />
                  {saving ? 'Salvando...' : 'Salvar Lançamentos'}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}