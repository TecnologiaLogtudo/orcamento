import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useLocation } from 'react-router-dom'; // Removed useNavigate
import { orcamentosAPI } from '../services/api';
import { categoriasAPI } from '../services/api';
import { Filter, RotateCcw, Save, Loader2, Send, Check, X, Trash2, Calendar } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ConfirmModal from './ConfirmModal';
import AlertModal from './AlertModal';
import PromptModal from './PromptModal';

export default function Lancamentos() {
  const { canEdit, canApprove, isAdmin } = useAuth(); // Removed user
  const location = useLocation();
  // const navigate = useNavigate(); // Removed navigate
  const navAppliedRef = useRef(false);
  const [notification, setNotification] = useState(null); // { type: 'success'|'error'|'info', message }

  // Modal States
  const [alertModal, setAlertModal] = useState({ isOpen: false, title: '', message: '' });
  const [confirmModal, setConfirmModal] = useState({ isOpen: false, title: '', message: '', onConfirm: () => {} });
  const [promptModal, setPromptModal] = useState({ isOpen: false, title: '', message: '', onConfirm: () => {} });

  const showAlert = (title, message) => setAlertModal({ isOpen: true, title, message });
  const showConfirm = (title, message, onConfirm) => setConfirmModal({ isOpen: true, title, message, onConfirm });
  const showPrompt = (title, message, onConfirm) => setPromptModal({ isOpen: true, title, message, onConfirm });

  const closeModal = () => {
    setAlertModal({ ...alertModal, isOpen: false });
    setConfirmModal({ ...confirmModal, isOpen: false });
    setPromptModal({ ...promptModal, isOpen: false });
  };

  const showNotification = (type, message, timeout = 4000) => {
    setNotification({ type, message });
    if (timeout > 0) {
      setTimeout(() => setNotification(null), timeout);
    }
  };
  const [orcamentos, setOrcamentos] = useState([]);
  // const [originalOrcamentos, setOriginalOrcamentos] = useState([]); // Removed unused state
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [modifiedIds, setModifiedIds] = useState(new Set());
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [filtros, setFiltros] = useState({
    ano: new Date().getFullYear(),
    mes: new Date().getMonth() + 1,
    master: '',
    uf: '',
    categoria: '',
    status: '',
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
  
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
  const [batchCategorias, setBatchCategorias] = useState([]);
  const [batchData, setBatchData] = useState({
    id_categoria: '',
    ano: new Date().getFullYear(),
    valor: '',
    meses: []
  });

  const loadRequestIdRef = useRef(0);

  const loadOrcamentos = useCallback(async (overrideFiltros = null) => {
    const usedFiltros = overrideFiltros || filtros;
    const reqId = ++loadRequestIdRef.current;
    console.log(`Lancamentos[req:${reqId}]: carregando orçamentos com filtros:`, usedFiltros);
    setLoading(true);
    try {
      let orcamentosCompletos = [];
      if (usedFiltros.status) {
        orcamentosCompletos = await orcamentosAPI.list(usedFiltros);
      } else {
        const categoriasResponse = await categoriasAPI.list({
          master: usedFiltros.master,
          uf: usedFiltros.uf,
          categoria: usedFiltros.categoria,
        });
        const todasCategorias = Array.isArray(categoriasResponse) ? categoriasResponse : [];

        const orcamentosResponse = await orcamentosAPI.list({
          ano: usedFiltros.ano,
          mes: usedFiltros.mes,
          master: usedFiltros.master,
          uf: usedFiltros.uf,
          categoria: usedFiltros.categoria,
          status: usedFiltros.status,
        });
        const orcamentosExistentes = Array.isArray(orcamentosResponse) ? orcamentosResponse : [];
        const orcamentosMap = new Map(orcamentosExistentes.map(o => [o.id_categoria, o]));

        orcamentosCompletos = todasCategorias.map(cat => {
          const orcamentoExistente = orcamentosMap.get(cat.id_categoria);
          return orcamentoExistente || {
            id_categoria: cat.id_categoria,
            categoria: cat,
            mes: usedFiltros.mes,
            ano: usedFiltros.ano,
            orcado: 0,
            realizado: 0,
            dif: 0,
            status: 'rascunho'
          };
        });
      }

      // Se outra requisição começou depois dessa, descartar esta resposta
      if (reqId !== loadRequestIdRef.current) {
        console.log(`Lancamentos[req:${reqId}]: resposta descartada (req atual: ${loadRequestIdRef.current})`);
        return;
      }

      setOrcamentos(orcamentosCompletos);
      console.log(`Lancamentos[req:${reqId}]: orçamentos carregados — total:`, orcamentosCompletos.length, 'filtros usados:', usedFiltros);
      // setOriginalOrcamentos(JSON.parse(JSON.stringify(orcamentosCompletos))); // Removed unused state
      setModifiedIds(new Set());
      setSelectedIds(new Set());
    } catch (error) {
      console.error('Erro ao carregar orçamentos:', error);
    } finally {
      // Somente limpar loading se esta requisição for a última
      if (reqId === loadRequestIdRef.current) setLoading(false);
    }
  }, [
    filtros,
    setLoading,
    setOrcamentos,
    setModifiedIds,
    setSelectedIds,
    // opcoesFiltro.meses // Removed unnecessary dependency
  ]);

  const loadInitialData = useCallback(async () => {
    const stateFilters = location?.state;
    if (stateFilters && !navAppliedRef.current) {
      try {
        const newFilters = {
          ano: new Date().getFullYear(),
          mes: new Date().getMonth() + 1,
          master: '',
          uf: '',
          categoria: '',
          status: '',
          ...stateFilters,
        };
        setFiltros(newFilters);
        navAppliedRef.current = true;
        
        try {
          const url = window.location.pathname + window.location.search + window.location.hash;
          window.history.replaceState(null, document.title, url);
        } catch (err) {
          console.error('Falha ao limpar history.state via replaceState:', err);
        }
        
        // Carga de orçamentos removida daqui, será tratada pelo useEffect de filtros
      } catch (error) {
        console.error('Erro ao aplicar filtros do location.state:', error);
      }
    }

    try {
      const data = await orcamentosAPI.getFiltros();
      const currentYear = new Date().getFullYear();
      const startYear = 2026;
      const windowLength = 6;
      const windowStart = Math.max(startYear, currentYear);
      const futureYears = Array.from({ length: windowLength }, (_, i) => windowStart + i);
      const years = Array.from(new Set([currentYear, ...(data.anos || []), ...futureYears])).sort((a, b) => a - b);

      setOpcoesFiltro(prev => ({
        ...prev,
        ...data,
        anos: years,
        categorias: data.categorias || [],
      }));
      if (!navAppliedRef.current && years.length > 0) {
        const defaultYear = years.includes(windowStart) ? windowStart : years[0];
        setFiltros(prev => {
          if (prev.ano === defaultYear) return prev;
          return { ...prev, ano: defaultYear };
        });
      }
    } catch (error) {
      console.error('Erro ao carregar filtros:', error);
    }
  }, [location?.state, setFiltros, setOpcoesFiltro]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  useEffect(() => {
    loadOrcamentos();
  }, [filtros, loadOrcamentos]);


  // Log de todas as alterações em `filtros` para diagnóstico
  useEffect(() => {
    console.log('Lancamentos: filtros alterados ->', filtros);
  }, [filtros]);

  const toggleSelect = (id) => {
    setSelectedIds(prev => {
      const s = new Set(prev);
      if (s.has(id)) s.delete(id);
      else s.add(id);
      return s;
    });
  };

  const toggleSelectAll = (checked) => {
    if (checked) {
      const eligible = orcamentos
        .filter(o => o.id_orcamento && o.status === 'aguardando_aprovacao')
        .map(o => o.id_orcamento);
      setSelectedIds(new Set(eligible));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleBatchApprove = async () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) {
      showAlert('Atenção', 'Nenhum orçamento selecionado para aprovação.');
      return;
    }

    showConfirm('Confirmar Aprovação', `Deseja realmente aprovar ${ids.length} orçamento(s)?`, async () => {
      setSaving(true);
      try {
        await orcamentosAPI.batchApprove(ids);
        showNotification('success', `${ids.length} orçamentos aprovados com sucesso.`);
        setSelectedIds(new Set());
        loadOrcamentos();
      } catch (error) {
        showNotification('error', 'Erro ao aprovar orçamentos: ' + (error.response?.data?.error || error.message));
      } finally {
        setSaving(false);
      }
    });
  };

  const handleBatchReprove = async () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) {
      showAlert('Atenção', 'Nenhum orçamento selecionado para reprovação.');
      return;
    }

    showPrompt('Motivo da Reprovação', 'Por favor, informe o motivo da reprovação para o lote:', async (motivo) => {
      if (!motivo || motivo.trim() === '') {
        closeModal();
        setTimeout(() => showAlert('Erro de Validação', 'O motivo da reprovação é obrigatório.'), 10);
        return;
      }
      closeModal();

      setTimeout(() => showConfirm('Confirmar Reprovação', `Deseja realmente reprovar ${ids.length} orçamentos com o motivo "${motivo}"?`, async () => {
        setSaving(true);
        try {
          await orcamentosAPI.batchReprove(ids, motivo);
          showNotification('success', `${ids.length} orçamentos reprovados com sucesso.`);
          setSelectedIds(new Set());
          loadOrcamentos();
        } catch (error) {
          showNotification('error', 'Erro ao reprovar orçamentos: ' + (error.response?.data?.error || error.message));
        } finally {
          setSaving(false);
        }
      }), 10);
    });
  };

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
      categoria: '',
      status: '',
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

        return updatedOrc;
      })
    );
    setModifiedIds(prevIds => new Set(prevIds).add(uniqueId));
  };

  const getMonthName = (mes) => {
    if (typeof mes === 'number') {
      const mesObj = opcoesFiltro.meses.find(m => m.valor === mes);
      return mesObj ? mesObj.nome : null;
    }
    return mes; // Assume it's already a valid name
  };

  const handleSendForApproval = async () => {
    const modifiedOrcamentos = orcamentos.filter(orc => {
      const uniqueId = orc.id_orcamento || `${orc.id_categoria}-${orc.mes}-${orc.ano}`;
      // Apenas rascunhos modificados
      return modifiedIds.has(uniqueId) && orc.status === 'rascunho';
    });

    if (modifiedOrcamentos.length === 0) {
      showNotification('info', 'Nenhum rascunho modificado para enviar.');
      return;
    }

    setSaving(true);
    try {
      // Passo 1: Salvar as alterações
      const orcamentosPayload = modifiedOrcamentos.map(orc => {
        const { ...rest } = orc; // Removed explicit destructuring of categoria and dif
        return {
          ...rest,
          mes: getMonthName(rest.mes),
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

      showNotification('success', `${modifiedOrcamentos.length} orçamento(s) enviado(s) para aprovação com sucesso!`);
      loadOrcamentos();
    } catch (error) {
        showNotification('error', 'Erro ao enviar para aprovação: ' + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const handleSaveChanges = async () => {
    const modifiedOrcamentos = orcamentos.filter(orc => {
      const uniqueId = orc.id_orcamento || `${orc.id_categoria}-${orc.mes}-${orc.ano}`;
      return modifiedIds.has(uniqueId) && orc.status === 'reprovado';
    });

    if (modifiedOrcamentos.length === 0) {
      showNotification('info', 'Nenhum orçamento reprovado modificado para reenviar.');
      return;
    }

    setSaving(true);
    try {
      // Passo 1: Salvar as alterações (sem mudar o status aqui)
      const orcamentosPayload = modifiedOrcamentos.map(orc => {
        const { ...rest } = orc; // Removed explicit destructuring of categoria, dif, and status
        return {
          ...rest,
          mes: getMonthName(rest.mes),
          id_orcamento: rest.id_orcamento // Approved budgets already have an ID
        };
      });

      await orcamentosAPI.batchUpdate(orcamentosPayload);
      
      // Passo 2: Submeter os mesmos orçamentos para aprovação
      const idsToSubmit = modifiedOrcamentos.map(o => o.id_orcamento);
      if (idsToSubmit.length > 0) {
        await orcamentosAPI.batchSubmit(idsToSubmit);
      }

      showNotification('success', `${modifiedOrcamentos.length} orçamento(s) reenviado(s) para aprovação com sucesso!`);
      loadOrcamentos();
    } catch (error) {
        showNotification('error', 'Erro ao reenviar para aprovação: ' + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const handleSavePending = async () => {
    const modifiedOrcamentos = orcamentos.filter(orc => {
      const uniqueId = orc.id_orcamento || `${orc.id_categoria}-${orc.mes}-${orc.ano}`;
      return modifiedIds.has(uniqueId) && orc.status === 'aguardando_aprovacao';
    });

    if (modifiedOrcamentos.length === 0) {
      showNotification('info', 'Nenhum orçamento modificado para salvar.');
      return;
    }

    setSaving(true);
    try {
      const orcamentosPayload = modifiedOrcamentos.map(orc => {
        const { ...rest } = orc;
        return {
          ...rest,
          mes: getMonthName(rest.mes),
          id_orcamento: rest.id_orcamento
        };
      });

      await orcamentosAPI.batchUpdate(orcamentosPayload);
      
      showNotification('success', `${modifiedOrcamentos.length} orçamento(s) atualizado(s) com sucesso!`);
      loadOrcamentos();
    } catch (error) {
        showNotification('error', 'Erro ao salvar alterações: ' + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id_orcamento) => {
    showConfirm('Confirmar Exclusão', 'Tem certeza que deseja excluir este orçamento? Esta ação não pode ser desfeita.', async () => {
      setSaving(true);
      try {
        await orcamentosAPI.delete(id_orcamento);
        showNotification('success', 'Orçamento excluído com sucesso.');
        loadOrcamentos();
      } catch (error) {
        showNotification('error', 'Erro ao excluir orçamento: ' + (error.response?.data?.error || error.message));
      } finally {
        setSaving(false);
      }
    });
  };

  const handleSaveRealizado = async () => {
    const modifiedOrcamentos = orcamentos.filter(orc => {
      const uniqueId = orc.id_orcamento || `${orc.id_categoria}-${orc.mes}-${orc.ano}`;
      // Only approved items that are within the edit window and have been modified
      return modifiedIds.has(uniqueId) && orc.status === 'aprovado' && isWithinRealizadoEditWindow(orc.mes, orc.ano);
    });

    if (modifiedOrcamentos.length === 0) {
      showNotification('info', 'Nenhum valor realizado modificado para salvar.');
      return;
    }

    setSaving(true);
    try {
      const orcamentosPayload = modifiedOrcamentos.map(orc => {
        const { ...rest } = orc; // Removed explicit destructuring of categoria and dif
        return {
          ...rest,
          mes: getMonthName(rest.mes),
          id_orcamento: rest.id_orcamento // It must have an ID as it is approved
        };
      });

      await orcamentosAPI.batchUpdate(orcamentosPayload);
      
      showNotification('success', `${modifiedOrcamentos.length} orçamento(s) atualizados com sucesso!`);
      loadOrcamentos(); // Reload to show fresh data
    } catch (error) {
        showNotification('error', 'Erro ao salvar valores realizados: ' + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (orcamentoId, newStatus) => {
    if (newStatus === 'reprovado') {
      showPrompt('Motivo da Reprovação', 'Por favor, informe o motivo da reprovação:', async (motivo) => {
        if (!motivo || motivo.trim() === '') {
          closeModal();
          setTimeout(() => showAlert('Erro de Validação', 'O motivo da reprovação é obrigatório.'), 10);
          return;
        }
        closeModal();
        
        setSaving(true);
        try {
          await orcamentosAPI.reprovar(orcamentoId, motivo);
          showNotification('success', 'Orçamento reprovado com sucesso!');
          loadOrcamentos();
        } catch (error) {
          showNotification('error', 'Erro ao reprovar orçamento: ' + (error.response?.data?.error || error.message));
        } finally {
          setSaving(false);
        }
      });
    } else if (newStatus === 'aprovado') {
      showConfirm('Confirmar Aprovação', 'Deseja realmente aprovar este orçamento?', async () => {
        setSaving(true);
        try {
          await orcamentosAPI.aprovar(orcamentoId);
          showNotification('success', 'Orçamento aprovado com sucesso!');
          loadOrcamentos();
        } catch (error) {
          showNotification('error', 'Erro ao aprovar orçamento: ' + (error.response?.data?.error || error.message));
        } finally {
          setSaving(false);
        }
      });
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value || 0);
  };

  // Retorna o número do mês (1-12) a partir do valor que pode ser número ou nome.
  const getMonthNumber = (mes) => {
    if (!mes && mes !== 0) return null;
    if (typeof mes === 'number') return mes;
    const found = opcoesFiltro.meses.find(m => m.nome.toLowerCase() === String(mes).toLowerCase());
    return found ? found.valor : null;
  };

  // Verifica se estamos dentro do prazo para editar o campo 'realizado' após aprovação:
  // até o 5º dia útil do mês seguinte ao mês do orçamento.
  const isWithinRealizadoEditWindow = (mes, ano) => {
    const monthNum = getMonthNumber(mes);
    if (!monthNum || !ano) return false;

    // Próximo mês e ano
    const nextMonthIndex = monthNum === 12 ? 0 : monthNum; // Date monthIndex (0-11)
    const nextYear = monthNum === 12 ? ano + 1 : ano;

    let businessDays = 0;
    let day = 1;
    let fifthBusinessDate = null;
    while (businessDays < 5 && day <= 31) {
      const d = new Date(nextYear, nextMonthIndex, day);
      const dow = d.getDay(); // 0 = Sunday, 6 = Saturday
      if (dow !== 0 && dow !== 6) {
        businessDays += 1;
        if (businessDays === 5) {
          fifthBusinessDate = d;
          break;
        }
      }
      day += 1;
    }

    if (!fifthBusinessDate) return false;

    const now = new Date();
    const endOfFifth = new Date(fifthBusinessDate.getFullYear(), fifthBusinessDate.getMonth(), fifthBusinessDate.getDate(), 23, 59, 59, 999);
    return now <= endOfFifth;
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

  const handleOpenBatchModal = async () => {
    setIsBatchModalOpen(true);
    // Reset form
    setBatchData({
      id_categoria: '',
      ano: filtros.ano || new Date().getFullYear(),
      valor: '',
      meses: []
    });
    
    // Carregar todas as categorias para o select
    try {
      const cats = await categoriasAPI.list();
      setBatchCategorias(cats);
    } catch (error) {
      showNotification('error', 'Erro ao carregar lista de categorias.');
    }
  };

  const handleBatchSubmit = async () => {
    if (!batchData.id_categoria || !batchData.valor || batchData.meses.length === 0) {
      showAlert('Campos Obrigatórios', 'Selecione a categoria, o valor e pelo menos um mês.');
      return;
    }

    setSaving(true);
    try {
      const payload = batchData.meses.map(mes => ({
        id_categoria: parseInt(batchData.id_categoria),
        mes: mes, // Backend aceita número ou nome, mas número é mais seguro aqui se o backend converter
        ano: parseInt(batchData.ano),
        orcado: parseFloat(batchData.valor),
        status: 'aguardando_aprovacao' // Novos lançamentos entram como aguardando aprovação
      }));

      await orcamentosAPI.batchUpdate(payload);
      
      showNotification('success', `${payload.length} orçamentos lançados com sucesso!`);
      setIsBatchModalOpen(false);
      loadOrcamentos(); // Recarregar grid
    } catch (error) {
      showNotification('error', 'Erro ao realizar lançamento múltiplo: ' + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const toggleBatchMonth = (mesValor) => {
    setBatchData(prev => {
      const newMeses = prev.meses.includes(mesValor)
        ? prev.meses.filter(m => m !== mesValor)
        : [...prev.meses, mesValor].sort((a, b) => a - b);
      return { ...prev, meses: newMeses };
    });
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
      <AlertModal
        isOpen={alertModal.isOpen}
        onClose={closeModal}
        title={alertModal.title}
        message={alertModal.message}
      />
      <ConfirmModal
        isOpen={confirmModal.isOpen}
        onClose={closeModal}
        title={confirmModal.title}
        message={confirmModal.message}
        onConfirm={confirmModal.onConfirm}
      />
      <PromptModal
        isOpen={promptModal.isOpen}
        onClose={closeModal}
        title={promptModal.title}
        message={promptModal.message}
        onConfirm={promptModal.onConfirm}
      />

      {notification && (
        <div className={`fixed right-4 top-4 z-50 max-w-sm w-full shadow-lg rounded-md p-3 text-sm font-medium ${notification.type === 'success' ? 'bg-green-50 text-green-800' : notification.type === 'error' ? 'bg-red-50 text-red-800' : 'bg-blue-50 text-blue-800'}`}>
          {notification.message}
        </div>
      )}
      {/* Header e Filtros */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <h1 className="text-2xl font-bold text-gray-900">Lançamentos</h1>
          <div className="flex gap-2">
            {isAdmin() && (
              <button
                onClick={handleOpenBatchModal}
                className="inline-flex items-center gap-2 px-4 py-2 border border-indigo-600 text-sm font-medium rounded-md text-indigo-600 bg-white hover:bg-indigo-50"
              >
                <Calendar size={16} />
                Lançamento Múltiplo
              </button>
            )}
            <button
              onClick={handleLimparFiltros}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <RotateCcw size={16} />
              Limpar Filtros
            </button>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-6 gap-4">
          <select name="ano" value={filtros.ano} onChange={handleFiltroChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
            {opcoesFiltro.anos?.map(y => <option key={`ano-${y}`} value={y}>{y}</option>)}
          </select>
          <select name="mes" value={filtros.mes} onChange={handleFiltroChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
            { !canEdit() && <option value="">Todos os Meses</option> }
            {opcoesFiltro.meses.map(m => <option key={`mes-${m.valor}`} value={m.valor}>{m.nome}</option>)}
          </select>
          <select name="status" value={filtros.status} onChange={handleFiltroChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
            <option value="">Todos os Status</option>
            {opcoesFiltro.status?.map(s => <option key={`status-${s}`} value={s}>{(s).replace(/_/g, ' ')}</option>)}
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

        {isAdmin() && modifiedIds.size > 0 && orcamentos.some(o => modifiedIds.has(o.id_orcamento || `${o.id_categoria}-${o.mes}-${o.ano}`) && o.status === 'rascunho') && (
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
        {isAdmin() && modifiedIds.size > 0 && orcamentos.some(o => modifiedIds.has(o.id_orcamento || `${o.id_categoria}-${o.mes}-${o.ano}`) && o.status === 'reprovado') && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleSaveChanges}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <Send size={20} />
              )}
              Reenviar para Aprovação
            </button>
          </div>
        )}
        {isAdmin() && modifiedIds.size > 0 && orcamentos.some(o => {
          const uniqueId = o.id_orcamento || `${o.id_categoria}-${o.mes}-${o.ano}`;
          return modifiedIds.has(uniqueId) && o.status === 'aguardando_aprovacao';
        }) && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleSavePending}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? <Loader2 size={20} className="animate-spin" /> : <Save size={20} />}
              Salvar Alterações (Aguardando)
            </button>
          </div>
        )}
        {canEdit() && modifiedIds.size > 0 && orcamentos.some(o => {
          const uniqueId = o.id_orcamento || `${o.id_categoria}-${o.mes}-${o.ano}`;
          return modifiedIds.has(uniqueId) && o.status === 'aprovado' && isWithinRealizadoEditWindow(o.mes, o.ano);
        }) && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleSaveRealizado}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <Save size={20} />
              )}
              Salvar Realizado
            </button>
          </div>
        )}
        {canApprove() && selectedIds.size > 0 && (
          <div className="mt-4 flex justify-end gap-2">
            <button
              onClick={handleBatchApprove}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {saving ? <Loader2 size={18} className="animate-spin" /> : <Check size={18} />}
              Aprovar Selecionados ({selectedIds.size})
            </button>
            <button
              onClick={handleBatchReprove}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {saving ? <Loader2 size={18} className="animate-spin" /> : <X size={18} />}
              Reprovar Selecionados ({selectedIds.size})
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
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                <input
                  type="checkbox"
                  onChange={(e) => toggleSelectAll(e.target.checked)}
                  checked={orcamentos.length > 0 && Array.from(selectedIds).length > 0 && orcamentos.filter(o => o.id_orcamento && o.status === 'aguardando_aprovacao').length === Array.from(selectedIds).length}
                />
              </th>
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
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(orc.id_orcamento)}
                    disabled={!orc.id_orcamento || orc.status !== 'aguardando_aprovacao'}
                    onChange={() => toggleSelect(orc.id_orcamento)}
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{orc.categoria?.master || ''}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{orc.categoria?.grupo || ''}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{orc.categoria?.uf || ''}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                  {/* Regra de edição: Apenas admins podem editar orçamentos reprovados. Outros status editáveis seguem a regra `canEdit`. */}
                  {canEdit() && (orc.status !== 'aprovado' && (isAdmin() || orc.status !== 'reprovado')) ? (
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
                  {canEdit() && orc.status === 'aprovado' && isWithinRealizadoEditWindow(orc.mes, orc.ano) ? (
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
                        <button onClick={() => handleStatusChange(orc.id_orcamento, 'reprovado')} className="text-red-600 hover:text-red-900" title="Reprovar">
                          <X size={18} />
                        </button>
                      </>
                    )}
                    {/* Ações do Admin (Delete/Edit Pending) */}
                    {isAdmin() && orc.status === 'aguardando_aprovacao' && (
                      <button onClick={() => handleDelete(orc.id_orcamento)} className="text-red-600 hover:text-red-900" title="Excluir">
                        <Trash2 size={18} />
                      </button>
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

      {/* Modal de Lançamento Múltiplo */}
      {isBatchModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">Lançamento Múltiplo de Orçamento</h3>
              <button onClick={() => setIsBatchModalOpen(false)} className="text-gray-400 hover:text-gray-500">
                <X size={24} />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Categoria</label>
                  <select
                    value={batchData.id_categoria}
                    onChange={(e) => setBatchData({...batchData, id_categoria: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">Selecione uma categoria...</option>
                    {batchCategorias.map(cat => (
                      <option key={cat.id_categoria} value={cat.id_categoria}>
                        {cat.master} - {cat.grupo} ({cat.uf})
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ano</label>
                  <select
                    value={batchData.ano}
                    onChange={(e) => setBatchData({...batchData, ano: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    {opcoesFiltro.anos?.map(y => <option key={`batch-ano-${y}`} value={y}>{y}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Valor Orçado (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={batchData.valor}
                    onChange={(e) => setBatchData({...batchData, valor: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="0,00"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Meses a Lançar</label>
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                  {opcoesFiltro.meses.map(m => (
                    <label key={`batch-mes-${m.valor}`} className="flex items-center space-x-2 p-2 border rounded hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={batchData.meses.includes(m.valor)}
                        onChange={() => toggleBatchMonth(m.valor)}
                        className="rounded text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="text-sm text-gray-700">{m.nome}</span>
                    </label>
                  ))}
                </div>
                <div className="mt-2 flex gap-2 text-xs">
                  <button onClick={() => setBatchData(prev => ({...prev, meses: opcoesFiltro.meses.map(m => m.valor)}))} className="text-indigo-600 hover:text-indigo-800">Marcar Todos</button>
                  <span className="text-gray-300">|</span>
                  <button onClick={() => setBatchData(prev => ({...prev, meses: []}))} className="text-gray-500 hover:text-gray-700">Desmarcar Todos</button>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setIsBatchModalOpen(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleBatchSubmit}
                disabled={saving}
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                Lançar Orçamentos
              </button>
            </div>
          </div>
        </div>
      )}
    </div >
  );
}