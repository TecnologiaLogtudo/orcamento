import { useState, useEffect } from 'react';
import { relatoriosAPI, dashboardAPI } from '../services/api';
import { FileDown, FileSpreadsheet } from 'lucide-react';

export default function Relatorios() {
  const [filtros, setFiltros] = useState({ ano: new Date().getFullYear() });
  const [filtrosDisponiveis, setFiltrosDisponiveis] = useState({});
  const [dados, setDados] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadFiltros();
  }, []);

  const loadFiltros = async () => {
    try {
      const data = await dashboardAPI.getFiltros();
      setFiltrosDisponiveis(data);
    } catch (error) {
      console.error('Erro ao carregar filtros');
    }
  };

  const loadDados = async () => {
    try {
      setLoading(true);
      const data = await relatoriosAPI.getData(filtros);
      setDados(data);
    } catch (error) {
      alert('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleExportExcel = async () => {
    try {
      await relatoriosAPI.exportExcel(filtros);
    } catch (error) {
      alert('Erro ao exportar Excel');
    }
  };

  const handleExportPDF = async () => {
    try {
      await relatoriosAPI.exportPDF(filtros);
    } catch (error) {
      alert('Erro ao exportar PDF');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Relatórios</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <select
            value={filtros.ano || ''}
            onChange={(e) => setFiltros({...filtros, ano: e.target.value ? parseInt(e.target.value) : undefined})}
            className="px-4 py-2 border rounded-lg"
          >
            <option value="">Todos os Anos</option>
            {filtrosDisponiveis.anos?.map(ano => (
              <option key={ano} value={ano}>{ano}</option>
            ))}
          </select>

          <select
            value={filtros.categoria || ''}
            onChange={(e) => setFiltros({...filtros, categoria: e.target.value})}
            className="px-4 py-2 border rounded-lg"
          >
            <option value="">Todas as Categorias</option>
            {filtrosDisponiveis.categorias?.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          <button
            onClick={loadDados}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Buscar
          </button>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleExportExcel}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <FileSpreadsheet size={20} />
            Exportar Excel
          </button>
          <button
            onClick={handleExportPDF}
            className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            <FileDown size={20} />
            Exportar PDF
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : dados.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Categoria</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grupo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mês</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Orçado</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Realizado</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Diferença</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {dados.map((item, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 text-sm">{item.categoria}</td>
                  <td className="px-6 py-4 text-sm">{item.grupo}</td>
                  <td className="px-6 py-4 text-sm">{item.mes}</td>
                  <td className="px-6 py-4 text-sm text-right">
                    {new Intl.NumberFormat('pt-BR', {style: 'currency', currency: 'BRL'}).format(item.total_orcado)}
                  </td>
                  <td className="px-6 py-4 text-sm text-right">
                    {new Intl.NumberFormat('pt-BR', {style: 'currency', currency: 'BRL'}).format(item.total_realizado)}
                  </td>
                  <td className={`px-6 py-4 text-sm text-right font-semibold ${item.total_dif >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {new Intl.NumberFormat('pt-BR', {style: 'currency', currency: 'BRL'}).format(item.total_dif)}
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