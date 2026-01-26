import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SubmissionsLog from './SubmissionsLog';
import { useState } from 'react';
import Modal from './Modal';
import { Check, X, Calendar } from 'lucide-react';
import { orcamentosAPI } from '../services/api';
import PromptModal from './PromptModal';
import ConfirmModal from './ConfirmModal';

export default function Submissoes() {
  const navigate = useNavigate();
  const { canApprove } = useAuth();
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [promptModal, setPromptModal] = useState({ isOpen: false, title: '', message: '', onConfirm: () => {} });
  const [confirmModal, setConfirmModal] = useState({ isOpen: false, title: '', message: '', onConfirm: () => {} });
  const [refreshKey, setRefreshKey] = useState(0); // Para forçar recarga do log

  if (!canApprove()) {
    return (
      <div className="text-center py-16">
        <h2 className="text-2xl font-bold text-gray-900">Acesso negado</h2>
        <p className="text-gray-600 mt-2">Apenas gestores podem acessar esta página.</p>
      </div>
    );
  }

  const handleViewSubmission = (submission) => {
    setSelectedSubmission(submission);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedSubmission(null);
  };

  const groupOrcamentos = (orcamentos) => {
    if (!orcamentos) return [];
    const groups = {};
    orcamentos.forEach(orc => {
      // Chave composta para agrupar
      const key = `${orc.id_categoria}-${orc.ano}`;
      if (!groups[key]) {
        groups[key] = {
          ...orc,
          meses: []
        };
      }
      groups[key].meses.push({
        mes: orc.mes,
        orcado: orc.orcado,
        id_orcamento: orc.id_orcamento
      });
    });
    
    // Ordenar meses dentro dos grupos
    const monthOrder = {
      'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
      'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
    };
    
    return Object.values(groups).map(g => ({
      ...g,
      meses: g.meses.sort((a, b) => monthOrder[a.mes] - monthOrder[b.mes])
    }));
  };

  const handleApproveAll = () => {
    if (!selectedSubmission) return;
    const ids = selectedSubmission.orcamentos.map(o => o.id_orcamento);
    
    setConfirmModal({
      isOpen: true,
      title: 'Aprovar Submissão',
      message: `Deseja aprovar todos os ${ids.length} orçamentos desta submissão?`,
      onConfirm: async () => {
        try {
          await orcamentosAPI.batchApprove(ids);
          alert('Orçamentos aprovados com sucesso!');
          closeModal();
          setRefreshKey(prev => prev + 1);
        } catch (error) {
          alert('Erro ao aprovar: ' + error.message);
        }
      }
    });
  };

  const handleReproveAll = () => {
    if (!selectedSubmission) return;
    const ids = selectedSubmission.orcamentos.map(o => o.id_orcamento);

    setPromptModal({
      isOpen: true,
      title: 'Reprovar Submissão',
      message: 'Informe o motivo da reprovação para todos os itens:',
      onConfirm: async (motivo) => {
        if (!motivo) return alert('Motivo é obrigatório');
        try {
          await orcamentosAPI.batchReprove(ids, motivo);
          alert('Orçamentos reprovados com sucesso!');
          closeModal();
          setPromptModal(prev => ({ ...prev, isOpen: false }));
          setRefreshKey(prev => prev + 1);
        } catch (error) {
          alert('Erro ao reprovar: ' + error.message);
        }
      }
    });
  };

  return (
    <div className="space-y-6">
      <PromptModal
        isOpen={promptModal.isOpen}
        onClose={() => setPromptModal(prev => ({ ...prev, isOpen: false }))}
        title={promptModal.title}
        message={promptModal.message}
        onConfirm={promptModal.onConfirm}
      />
      <ConfirmModal
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal(prev => ({ ...prev, isOpen: false }))}
        title={confirmModal.title}
        message={confirmModal.message}
        onConfirm={confirmModal.onConfirm}
      />

      <div>
        <h1 className="text-3xl font-bold text-gray-900">Submissões para Aprovação</h1>
        <p className="text-gray-600 mt-2">
          Acompanhe os orçamentos submetidos pelo administrador e clique para visualizá-los em Lançamentos.
        </p>
      </div>

      <SubmissionsLog key={refreshKey} onNavigateToLancamentos={handleViewSubmission} />

      {/* Modal de Visualização Detalhada */}
      {isModalOpen && selectedSubmission && (
        <Modal isOpen={isModalOpen} onClose={closeModal} maxWidth="max-w-4xl">
          <div className="w-full">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-bold text-gray-900">Detalhes da Submissão</h3>
                <p className="text-sm text-gray-500">
                  Enviado por: {selectedSubmission.admin_usuario || 'Sistema'} em {new Date(selectedSubmission.data || Date.now()).toLocaleDateString()}
                </p>
              </div>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-500">
                <X size={24} />
              </button>
            </div>

            <div className="max-h-[60vh] overflow-y-auto space-y-4 mb-6">
              {groupOrcamentos(selectedSubmission.orcamentos).map((grupo, idx) => (
                <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-3 pb-2 border-b border-gray-200">
                    <div>
                      <h4 className="font-semibold text-gray-800">{grupo.categoria_nome}</h4>
                      <p className="text-xs text-gray-500">{grupo.master} • {grupo.uf} • {grupo.grupo}</p>
                    </div>
                    <div className="flex items-center gap-2 text-sm font-medium text-indigo-600 mt-2 sm:mt-0">
                      <Calendar size={16} />
                      {grupo.ano}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                    {grupo.meses.map((mesItem, mIdx) => (
                      <div key={mIdx} className="bg-white p-2 rounded border border-gray-100 shadow-sm flex flex-col">
                        <span className="text-xs text-gray-500 uppercase font-bold">{mesItem.mes}</span>
                        <span className="text-sm font-semibold text-gray-900">
                          {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(mesItem.orcado)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
              <button
                onClick={handleReproveAll}
                className="inline-flex items-center gap-2 px-4 py-2 border border-red-300 text-red-700 bg-white hover:bg-red-50 rounded-lg transition"
              >
                <X size={18} />
                Reprovar Tudo
              </button>
              <button
                onClick={handleApproveAll}
                className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white hover:bg-green-700 rounded-lg transition shadow-sm"
              >
                <Check size={18} />
                Aprovar Tudo
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
