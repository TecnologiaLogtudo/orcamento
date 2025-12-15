import { useState, useEffect } from 'react';
import { dashboardAPI } from '../services/api';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  AlertCircle,
  BarChart3,
  Calendar
} from 'lucide-react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
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
  ArcElement,
  Title,
  Tooltip,
  Legend
);

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [comparativo, setComparativo] = useState(null);
  const [distribuicaoCategoria, setDistribuicaoCategoria] = useState(null);
  const [distribuicaoCentroDeCusto, setDistribuicaoCentroDeCusto] = useState(null);
  const [filtros, setFiltros] = useState(() => {
    const savedFiltros = sessionStorage.getItem('dashboardFiltros');
    return savedFiltros ? JSON.parse(savedFiltros) : { ano: new Date().getFullYear() };
  });
  const [tempFiltros, setTempFiltros] = useState(() => {
    const savedFiltros = sessionStorage.getItem('dashboardFiltros');
    return savedFiltros ? JSON.parse(savedFiltros) : { ano: new Date().getFullYear() };
  });
  const [filtrosDisponiveis, setFiltrosDisponiveis] = useState({
    anos: [],
    categorias: [],
    ufs: [],
    centros_de_custo: []
  });

  useEffect(() => {
    // Carrega os filtros disponíveis (anos, categorias, UFs, grupos) uma vez
    loadFiltrosDisponiveis();
  }, []);

  useEffect(() => {
    // Recarrega os dados do dashboard sempre que os filtros mudarem
    loadDashboard();
    sessionStorage.setItem('dashboardFiltros', JSON.stringify(filtros));
  }, [filtros]); // Depende apenas dos filtros

  const loadFiltrosDisponiveis = async () => {
    try {
      const data = await dashboardAPI.getFiltros();
      setFiltrosDisponiveis(data);
      // Se não houver ano nos filtros disponíveis, use o ano atual
      if (data.anos && data.anos.length > 0 && !filtros.ano) {
        setFiltros(prev => ({
          ...prev,
          ano: data.anos[0]
        }));
        setTempFiltros(prev => ({
          ...prev,
          ano: data.anos[0]
        }));
      }
    } catch (error) {
      console.error('Erro ao carregar filtros:', error);
    }
  };

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [dashData, kpisData, comparativoData, distCatData, distCentroCustoData] = await Promise.all([
        dashboardAPI.getData(filtros),
        dashboardAPI.getKPIs(filtros.ano),
        dashboardAPI.getComparativo(filtros.ano),
        dashboardAPI.getDistribuicao({ ...filtros, tipo: 'categoria' }),
        dashboardAPI.getDistribuicao({ ...filtros, tipo: 'centro_custo' })
      ]);
      setDashboardData(dashData);
      setKpis(kpisData);
      setComparativo(comparativoData);
      setDistribuicaoCategoria(distCatData);
      setDistribuicaoCentroDeCusto(distCentroCustoData);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setTempFiltros(prev => ({
      ...prev,
      [key]: value || undefined
    }));
  };

  const handleApplyFilters = () => {
    setFiltros(tempFiltros);
  };

  const handleLimparFiltros = () => {
    const defaultFilters = {
      ano: filtrosDisponiveis.anos?.[0] || new Date().getFullYear()
    };
    setTempFiltros(defaultFilters);
    setFiltros(defaultFilters);
    sessionStorage.removeItem('dashboardFiltros');
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
  const monthlyData = dashboardData?.dados_mensais || [];
  const realizadoValues = monthlyData.map(d => d.realizado);

  // A média do realizado deve ser calculada apenas sobre meses com atividade (orçado > 0 ou realizado > 0)
  // para evitar que meses futuros (com valor 0) distorçam o resultado.
  const activeMonths = monthlyData.filter(d => d.orcado > 0 || d.realizado > 0);
  const averageRealizado = activeMonths.length > 0
    ? activeMonths.reduce((sum, d) => sum + d.realizado, 0) / activeMonths.length
    : 0;
  
  const averageLineData = new Array(monthlyData.length).fill(averageRealizado);

  const lineChartData = monthlyData.length > 0 ? {
    labels: monthlyData.map(d => d.mes.substring(0, 3)),
    datasets: [
      {
        label: 'Orçado',
        data: monthlyData.map(d => d.orcado),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4
      },
      {
        label: 'Realizado',
        data: realizadoValues,
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4
      },
      {
        label: 'Média Realizado',
        data: averageLineData,
        borderColor: 'rgb(249, 115, 22)',
        borderDash: [5, 5],
        fill: false,
        tension: 0,
        pointRadius: 0,
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

  // Dados para gráfico de pizza (Distribuição por Categoria)
  const pieCategoryData = distribuicaoCategoria?.dados ? {
    labels: distribuicaoCategoria.dados.map(d => d.nome),
    datasets: [
      {
        label: 'Orçado (%)',
        data: distribuicaoCategoria.dados.map(d => d.percentual),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(236, 72, 153, 0.8)',
          'rgba(14, 165, 233, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(16, 185, 129)',
          'rgb(249, 115, 22)',
          'rgb(168, 85, 247)',
          'rgb(236, 72, 153)',
          'rgb(14, 165, 233)',
          'rgb(34, 197, 94)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 2
      }
    ]
  } : null;

  // Dados para gráfico de pizza (Distribuição por Centro de Custo)
  const pieCentroDeCustoData = distribuicaoCentroDeCusto?.dados ? {
    labels: distribuicaoCentroDeCusto.dados.map(d => d.nome),
    datasets: [
      {
        label: 'Orçado (%)',
        data: distribuicaoCentroDeCusto.dados.map(d => d.percentual),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(236, 72, 153, 0.8)',
          'rgba(14, 165, 233, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(16, 185, 129)',
          'rgb(249, 115, 22)',
          'rgb(168, 85, 247)',
          'rgb(236, 72, 153)',
          'rgb(14, 165, 233)',
          'rgb(34, 197, 94)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 2
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

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return context.label + ': ' + context.parsed + '%';
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
          <div className="flex flex-wrap gap-2">
            <select
              value={tempFiltros.ano || ''}
              onChange={(e) => handleFilterChange('ano', e.target.value ? parseInt(e.target.value) : undefined)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            >
              {filtrosDisponiveis.anos.map(ano => (
                <option key={ano} value={ano}>{ano}</option>
              ))}
            </select>

            <select
              value={tempFiltros.categoria || ''}
              onChange={(e) => handleFilterChange('categoria', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            >
              <option value="">Todas as Categorias</option>
              {filtrosDisponiveis.categorias.map(categoria => (
                <option key={categoria} value={categoria}>{categoria}</option>
              ))}
            </select>

            <select
              value={tempFiltros.uf || ''}
              onChange={(e) => handleFilterChange('uf', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            >
              <option value="">Todos os UFs</option>
              {filtrosDisponiveis.ufs.map(uf => (
                <option key={uf} value={uf}>{uf}</option>
              ))}
            </select>

            <select
              value={tempFiltros.centro_custo || ''}
              onChange={(e) => handleFilterChange('centro_custo', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            >
              <option value="">Todos os Centros de Custo</option>
              {filtrosDisponiveis.centros_de_custo.map(cc => (
                <option key={cc} value={cc}>{cc}</option>
              ))}
            </select>

            <button
              onClick={handleApplyFilters}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium"
            >
              Aplicar Filtros
            </button>

            {(tempFiltros.categoria || tempFiltros.uf || tempFiltros.centro_custo) && (
              <button
                onClick={handleLimparFiltros}
                className="px-3 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm font-medium"
              >
                Limpar Filtros
              </button>
            )}
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
        {dashboardData?.mes_critico && dashboardData.mes_critico.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5 text-orange-500" />
              <h2 className="text-lg font-semibold text-gray-900">
                {dashboardData.mes_critico.length > 1 ? 'Meses Críticos' : 'Mês Crítico'}
              </h2>
            </div>
            <div className="space-y-4">
              {(() => {
                const sortOrder = { 'economia': 1, 'precisao': 2, 'gasto': 3, 'neutro': 4 };
                const sortedCriticos = [...dashboardData.mes_critico].sort((a, b) => (sortOrder[a.tipo] || 99) - (sortOrder[b.tipo] || 99));

                return sortedCriticos.map((critico, index) => {
                  const cardStyle = critico.tipo === 'economia'
                    ? 'bg-green-50 border-green-200'
                    : critico.tipo === 'gasto'
                      ? 'bg-red-50 border-red-200'
                      : critico.tipo === 'precisao'
                        ? 'bg-blue-50 border-blue-200'
                        : 'bg-orange-50 border-orange-200';

                  const title = critico.tipo === 'economia'
                    ? 'Mês de maior economia'
                    : critico.tipo === 'gasto'
                      ? 'Mês de maior gasto'
                      : critico.tipo === 'precisao'
                        ? 'Mês de Maior Precisão'
                        : 'Mês com gasto próximo ao orçado';

                  return (
                    <div key={index} className={`${cardStyle} rounded-lg p-4`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-sm text-gray-600 mb-1">{title}</p>
                          <p className="text-xl font-bold text-gray-900">
                            {critico.mes}
                          </p>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <p className={`text-lg font-semibold ${
                            critico.desvio > 0 ? 'text-green-600' : critico.desvio < 0 ? 'text-red-600' : 'text-gray-700'
                          }`}>
                            {formatCurrency(critico.desvio)}
                          </p>
                          <span className={`text-sm font-semibold ${ critico.percentual > 0 ? 'text-red-500' : critico.percentual < 0 ? 'text-green-500' : 'text-gray-500' }`}>
                            ({(parseFloat(critico.percentual) || 0).toFixed(2)}%)
                          </span>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-current opacity-50">
                        <span>Orçado: {formatCurrency(critico.orcado)}</span>
                        <span className="mx-2">|</span>
                        <span>Realizado: {formatCurrency(critico.realizado)}</span>
                      </div>
                    </div>
                  );
                });
              })()}
            </div>
          </div>
        )}

        {/* Top 5 Centros de Custo Críticos */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Top 5 Centros de Custo Críticos
          </h2>
          <div className="space-y-3">
            {dashboardData?.centros_custo_criticos?.map((item, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">{item.centro_custo}</span>
                  <div className="flex items-baseline gap-2">
                    <span className={`font-semibold ${
                      item.desvio >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(item.desvio)}
                    </span>
                    <span className={`text-sm font-semibold ${ item.percentual >= 0 ? 'text-red-500' : 'text-green-500' }`}>
                      ({(parseFloat(item.percentual) || 0).toFixed(2)}%)
                    </span>
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  <span>Orçado: {formatCurrency(item.orcado)}</span>
                  <span className="mx-2">|</span>
                  <span>Realizado: {formatCurrency(item.realizado)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Gráficos de Distribuição */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribuição por Categoria */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Distribuição por Categoria
          </h2>
          <div style={{ height: '300px' }}>
            {pieCategoryData && <Doughnut data={pieCategoryData} options={pieChartOptions} />}
          </div>
        </div>

        {/* Desempenho por Centro de custos */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Desempenho por Centro de custos
          </h2>
          <div style={{ height: '300px' }}>
            {pieCentroDeCustoData && <Doughnut data={pieCentroDeCustoData} options={pieChartOptions} />}
          </div>
        </div>
      </div>

      {/* Comparativo com Período Anterior */}
      {comparativo && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Comparativo: {comparativo.periodo_atual.ano} vs {comparativo.periodo_anterior.ano}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Total Orçado */}
            <div className="border rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">Total Orçado</p>
              <div className="space-y-2">
                <div>
                  <p className="text-xs text-gray-500 mb-1">{comparativo.periodo_atual.ano}</p>
                  <p className="text-xl font-bold text-gray-900">
                    {formatCurrency(comparativo.periodo_atual.dados.total_orcado)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">{comparativo.periodo_anterior.ano}</p>
                  <p className="text-xl font-bold text-gray-600">
                    {formatCurrency(comparativo.periodo_anterior.dados.total_orcado)}
                  </p>
                </div>
                <div className={`pt-2 border-t ${
                  comparativo.variacoes.total_orcado_pct >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  <p className="text-sm font-semibold">
                    {comparativo.variacoes.total_orcado_pct >= 0 ? '+' : ''}{(parseFloat(comparativo.variacoes.total_orcado_pct) || 0).toFixed(2)}%
                  </p>
                </div>
              </div>
            </div>

            {/* Total Realizado */}
            <div className="border rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">Total Realizado</p>
              <div className="space-y-2">
                <div>
                  <p className="text-xs text-gray-500 mb-1">{comparativo.periodo_atual.ano}</p>
                  <p className="text-xl font-bold text-gray-900">
                    {formatCurrency(comparativo.periodo_atual.dados.total_realizado)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">{comparativo.periodo_anterior.ano}</p>
                  <p className="text-xl font-bold text-gray-600">
                    {formatCurrency(comparativo.periodo_anterior.dados.total_realizado)}
                  </p>
                </div>
                <div className={`pt-2 border-t ${
                  comparativo.variacoes.total_realizado_pct >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  <p className="text-sm font-semibold">
                    {comparativo.variacoes.total_realizado_pct >= 0 ? '+' : ''}{(parseFloat(comparativo.variacoes.total_realizado_pct) || 0).toFixed(2)}%
                  </p>
                </div>
              </div>
            </div>

            {/* Desvio Total */}
            <div className="border rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">Desvio Total</p>
              <div className="space-y-2">
                <div>
                  <p className="text-xs text-gray-500 mb-1">{comparativo.periodo_atual.ano}</p>
                  <p className={`text-xl font-bold ${
                    comparativo.periodo_atual.dados.total_dif >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(comparativo.periodo_atual.dados.total_dif)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">{comparativo.periodo_anterior.ano}</p>
                  <p className={`text-xl font-bold ${
                    comparativo.periodo_anterior.dados.total_dif >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(comparativo.periodo_anterior.dados.total_dif)}
                  </p>
                </div>
                <div className={`pt-2 border-t ${
                  comparativo.variacoes.total_dif_pct >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  <p className="text-sm font-semibold">
                    {comparativo.variacoes.total_dif_pct >= 0 ? '+' : ''}{(parseFloat(comparativo.variacoes.total_dif_pct) || 0).toFixed(2)}%
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

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