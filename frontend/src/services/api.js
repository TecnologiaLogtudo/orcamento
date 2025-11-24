import axios from 'axios';

// ================== CONFIGURAÇÃO BASE ==================

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============= INTERCEPTORES =============

// Adicionar token JWT em todas as requisições
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Redirecionar ao login se o token for inválido/expirado
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      delete api.defaults.headers.common['Authorization'];
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ============= AUTENTICAÇÃO =============

export const authAPI = {
  login: async (email, senha) => {
    // Login agora sempre chama endpoint completo
    const response = await api.post('/login', { email, senha });
    return response.data;
  },

  setAuthToken: (token) => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  },

  getCurrentUser: async () => {
    const response = await api.get('/me');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete api.defaults.headers.common['Authorization'];
    window.location.href = '/login';
  },
};

// ============= USUÁRIOS =============

export const usuariosAPI = {
  list: async () => (await api.get('/usuarios')).data,
  create: async (data) => (await api.post('/usuarios', data)).data,
  update: async (id, data) => (await api.put(`/usuarios/${id}`, data)).data,
  delete: async (id) => (await api.delete(`/usuarios/${id}`)).data,
};

// ============= CATEGORIAS =============

export const categoriasAPI = {
  list: async (filtros = {}) => (await api.get('/categorias', { params: filtros })).data,
  get: async (id) => (await api.get(`/categorias/${id}`)).data,
  create: async (data) => (await api.post('/categorias', data)).data,
  update: async (id, data) => (await api.put(`/categorias/${id}`, data)).data,
  delete: async (id) => (await api.delete(`/categorias/${id}`)).data,
  import: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/categorias/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  getFiltros: async () => (await api.get('/categorias/filtros')).data,
};

// ============= ORÇAMENTOS =============

export const orcamentosAPI = {
  getFiltros: async () => (await api.get('/orcamentos/filtros')).data,
  list: async (filtros = {}) => {
    // O backend armazena o mês como nome (e.g., 'Janeiro').
    // Se o frontend passar um número, converte para o nome antes de chamar o endpoint.
    const MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];

    const params = { ...filtros };
    if (params.mes && typeof params.mes === 'number') {
      const m = params.mes;
      if (m >= 1 && m <= 12) params.mes = MESES[m - 1];
    }

    return (await api.get('/orcamentos', { params })).data;
  },
  getCategoriaAno: async (idCategoria, ano) =>
    (await api.get(`/orcamentos/categoria/${idCategoria}/ano/${ano}`)).data,
  createOrUpdate: async (data) => (await api.post('/orcamentos', data)).data,
  batchUpdate: async (orcamentos) => (await api.post('/orcamentos/batch', { orcamentos })).data,
  batchSubmit: async (ids) => {
    // aceita tanto um array de ids quanto um objeto { ids: [...] }
    const payload = Array.isArray(ids) ? { ids } : (ids || {});
    return (await api.post('/orcamentos/batch_submit', payload)).data;
  },
  batchApprove: async (ids) => {
    const payload = Array.isArray(ids) ? { ids } : (ids || {});
    return (await api.post('/orcamentos/batch_approve', payload)).data;
  },
  batchReprove: async (ids, motivo) => {
    const payload = Array.isArray(ids) ? { ids } : (ids || {});
    if (motivo) payload.motivo = motivo;
    return (await api.post('/orcamentos/batch_reprove', payload)).data;
  },
  aprovar: async (id) => (await api.post(`/orcamentos/${id}/aprovar`)).data,
  reprovar: async (id, motivo) => (await api.post(`/orcamentos/${id}/reprovar`, { motivo })).data,
  delete: async (id) => (await api.delete(`/orcamentos/${id}`)).data,
};

// ============= DASHBOARD =============

export const dashboardAPI = {
  getData: async (filtros = {}) => (await api.get('/dashboard', { params: filtros })).data,
  getKPIs: async (ano) => (await api.get('/dashboard/kpis', { params: { ano } })).data,
};

// ============= RELATÓRIOS =============

export const relatoriosAPI = {
  getData: async (filtros = {}) => (await api.get('/relatorios', { params: filtros })).data,

  exportExcel: async (filtros = {}) => {
    const response = await api.get('/relatorios/excel', {
      params: filtros,
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `relatorio_${new Date().toISOString().split('T')[0]}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    return response.data;
  },

  exportPDF: async (filtros = {}) => {
    const response = await api.get('/relatorios/pdf', {
      params: filtros,
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `relatorio_${new Date().toISOString().split('T')[0]}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    return response.data;
  },
};

// ============= LOGS =============

export const logsAPI = {
  list: async (filtros = {}) => (await api.get('/logs', { params: filtros })).data,
  get: async (id) => (await api.get(`/logs/${id}`)).data,
  getUserLogs: async (userId, params = {}) =>
    (await api.get(`/logs/usuario/${userId}`, { params })).data,
  getTableLogs: async (table, params = {}) =>
    (await api.get(`/logs/tabela/${table}`, { params })).data,
  getResumo: async () => (await api.get('/logs/resumo')).data,
  exportar: (filtros = {}) => {
    const params = new URLSearchParams(filtros);
    window.open(`${api.defaults.baseURL}/logs/exportar?${params}`);
  },
  search: async (criterios) => (await api.post('/logs/search', criterios)).data,
};

export default api;
