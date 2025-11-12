import { useState, useEffect } from 'react';
import { dashboardAPI, categoriasAPI } from '../services/api';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  AlertCircle,
  BarChart3,
  Calendar
} from 'lucide-react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [filtros, setFiltros] = useState({
    ano: new Date().getFullYear()
  });
  const [filtrosDisponiveis, setFiltrosDisponiveis] = useState({
    donos: [],
    tipos_despesa: [],
    ufs: [],
    grupos: []
  });

  useEffect(() => {
    // Carrega os filtros disponíveis (donos, tipos, etc) uma vez
    loadFiltrosDisponiveis();
  }, []);

  useEffect(() => {
    // Recarrega os dados do dashboard sempre que os filtros mudarem
    loadDashboard();
  }, [filtros]); // Depende apenas dos filtros

  const loadFiltrosDisponiveis = async () => {
    try {
      const data = await categoriasAPI.getFiltros();
      setFiltrosDisponiveis(data);
    } catch (error) {
      console.error('Erro ao carregar filtros:', error);
    }
  };

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [dashData, kpisData] = await Promise.all([
        dashboardAPI.getData(filtros),
        dashboardAPI.getKPIs(filtros) // Passar o objeto de filtros completo
      ]);
      setDashboardData(dashData);
      setKpis(kpisData);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFiltros(prev => ({
      ...prev,
      [key]: value || undefined
    }));
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatPercent = (value) => {
    return `${value.toFixed(2)}%`;
  };

  // Dados para gráfico de linha (Orçado vs Realizado)
  const lineChartData = dashboardData?.dados_mensais ? {
    labels: dashboardData.dados_mensais.map(d => d.mes.substring(0, 3)),
    datasets: [
      {
        label: 'Orçado',
        data: dashboardData.dados_mensais.map(d => d.orcado),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4
      },
      {
        label: 'Realizado',
        data: dashboardData.dados_mensais.map(d => d.realizado),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4
      }
    ]
  } : null;

  // Dados para gráfico de barras (Desvios)
  const barChartData = dashboardData?.dados_mensais ? {
    labels: dashboardData.dados_mensais.map(d => d.mes.substring(0, 3)),
    datasets: [
      {
        label: 'Desvio',
        data: dashboardData.dados_mensais.map(d => d.dif),
        backgroundColor: dashboardData.dados_mensais.map(d => 
          d.dif >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(239, 68, 68, 0.7)'
        ),
        borderColor: dashboardData.dados_mensais.map(d => 
          d.dif >= 0 ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)'
        ),
        borderWidth: 1
      }
    ]
  } : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            return formatCurrency(value);
          }
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const totais = dashboardData?.totais || {};

  return (
    <div className="space-y-6">
      {/* Header com Título e Filtros */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard Orçamentário</h1>
            <p className="text-gray-600 mt-1">Visão geral do desempenho orçamentário</p>
          </div>

          {/* Filtros */}
          <div className="flex flex-wrap gap-3">
            <select
              value={filtros.ano || ''}
              onChange={(e) => handleFilterChange('ano', e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {[2023, 2024, 2025, 2026].map(ano => (
                <option key={ano} value={ano}>{ano}</option>
              ))}
            </select>

            <select
              value={filtros.dono || ''}
              onChange={(e) => handleFilterChange('dono', e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Todos os Donos</option>
              {filtrosDisponiveis.donos.map(dono => (
                <option key={dono} value={dono}>{dono}</option>
              ))}
            </select>

            <select
              value={filtros.tipo_despesa || ''}
              onChange={(e) => handleFilterChange('tipo_despesa', e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Todos os Tipos</option>
              {filtrosDisponiveis.tipos_despesa.map(tipo => (
                <option key={tipo} value={tipo}>{tipo}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Cards de KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Orçado */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Orçado</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(totais.total_orcado || 0)}
              </p>
            </div>
            <div className="bg-blue-100 p-3 rounded-lg">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        {/* Total Realizado */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Realizado</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(totais.total_realizado || 0)}
              </p>
            </div>
            <div className="bg-green-100 p-3 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        {/* Desvio */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Desvio Total</p>
              <p className={`text-2xl font-bold ${
                (totais.total_dif || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(totais.total_dif || 0)}
              </p>
            </div>
            <div className={`${
              (totais.total_dif || 0) >= 0 ? 'bg-green-100' : 'bg-red-100'
            } p-3 rounded-lg`}>
              {(totais.total_dif || 0) >= 0 ? (
                <TrendingUp className="w-6 h-6 text-green-600" />
              ) : (
                <TrendingDown className="w-6 h-6 text-red-600" />
              )}
            </div>
          </div>
        </div>

        {/* % Execução */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">% Execução</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatPercent(totais.percentual_execucao || 0)}
              </p>
            </div>
            <div className="bg-purple-100 p-3 rounded-lg">
              <BarChart3 className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico de Linha */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Orçado vs Realizado (Mensal)
          </h2>
          <div style={{ height: '300px' }}>
            {lineChartData && <Line data={lineChartData} options={chartOptions} />}
          </div>
        </div>

        {/* Gráfico de Barras */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Desvios por Mês
          </h2>
          <div style={{ height: '300px' }}>
            {barChartData && <Bar data={barChartData} options={chartOptions} />}
          </div>
        </div>
      </div>

      {/* Mês Crítico e Grupos Críticos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mês Crítico */}
        {dashboardData?.mes_critico && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5 text-orange-500" />
              <h2 className="text-lg font-semibold text-gray-900">Mês Crítico</h2>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Maior Desvio</p>
              <p className="text-xl font-bold text-gray-900">
                {dashboardData.mes_critico.mes}
              </p>
              <p className={`text-lg font-semibold mt-2 ${
                dashboardData.mes_critico.desvio >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(dashboardData.mes_critico.desvio)}
              </p>
            </div>
          </div>
        )}

        {/* Top 5 Grupos Críticos */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Top 5 Grupos com Maior Desvio
          </h2>
          <div className="space-y-3">
            {dashboardData?.grupos_criticos?.map((grupo, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-900">{grupo.grupo}</span>
                <span className={`font-semibold ${
                  grupo.desvio >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(grupo.desvio)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Resumo de KPIs do Sistema */}
      {kpis && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Resumo do Sistema</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">{kpis.total_categorias}</p>
              <p className="text-sm text-gray-600 mt-1">Categorias</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{kpis.total_orcamentos}</p>
              <p className="text-sm text-gray-600 mt-1">Orçamentos</p>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <p className="text-2xl font-bold text-yellow-600">{kpis.aguardando_aprovacao}</p>
              <p className="text-sm text-gray-600 mt-1">Aguardando Aprovação</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-2xl font-bold text-purple-600">{kpis.aprovados}</p>
              <p className="text-sm text-gray-600 mt-1">Aprovados</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}