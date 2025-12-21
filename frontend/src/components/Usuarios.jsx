import { useState, useEffect } from 'react';
import { usuariosAPI } from '../services/api';
import { useAuth } from '../context/AuthContext'; // Import useAuth

export default function Usuarios() {
  const { user, isAdmin } = useAuth(); // Use useAuth to get user and isAdmin
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false); // Renamed from showModal
  const [showEditModal, setShowEditModal] = useState(false); // New state for edit modal
  const [editingUser, setEditingUser] = useState(null); // New state to hold user being edited
  const [formData, setFormData] = useState({ nome: '', email: '', senha: '', papel: 'visualizador' });

  useEffect(() => {
    loadUsuarios();
  }, []);

  const loadUsuarios = async () => {
    try {
      const data = await usuariosAPI.list();
      setUsuarios(data);
    } catch (error) {
      alert('Erro ao carregar usuários: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubmit = async (e) => { // Renamed from handleSubmit
    e.preventDefault();
    try {
      await usuariosAPI.create(formData);
      alert('Usuário criado com sucesso!');
      setShowCreateModal(false);
      setFormData({ nome: '', email: '', senha: '', papel: 'visualizador' });
      loadUsuarios();
    } catch (error) {
      alert('Erro ao criar usuário: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleEditClick = (user) => {
    setEditingUser(user);
    setFormData({ // Pre-fill form with user data, but clear password
      nome: user.nome,
      email: user.email,
      papel: user.papel,
      senha: '' // Password should not be pre-filled for security
    });
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editingUser) return;

    try {
      const dataToUpdate = { ...formData };
      if (!dataToUpdate.senha) { // If password field is empty, do not send it
        delete dataToUpdate.senha;
      }
      await usuariosAPI.update(editingUser.id_usuario, dataToUpdate);
      alert('Usuário atualizado com sucesso!');
      setShowEditModal(false);
      setEditingUser(null);
      setFormData({ nome: '', email: '', senha: '', papel: 'visualizador' });
      loadUsuarios();
    } catch (error) {
      alert('Erro ao atualizar usuário: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleDelete = async (id) => {
    // Prevent admin from deleting themselves
    if (user && user.id_usuario === id) {
      alert('Você não pode deletar seu próprio usuário.');
      return;
    }
    if (!window.confirm('Tem certeza que deseja deletar este usuário?')) return;
    try {
      await usuariosAPI.delete(id);
      alert('Usuário deletado com sucesso!');
      loadUsuarios();
    } catch (error) {
      alert('Erro ao deletar usuário: ' + (error.response?.data?.error || error.message));
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Usuários</h1>
          {isAdmin && ( // Only show "Novo Usuário" button if admin
            <button
              onClick={() => { setShowCreateModal(true); setFormData({ nome: '', email: '', senha: '', papel: 'visualizador' }); }}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Novo Usuário
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Papel</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {usuarios.map(u => ( // Changed 'user' to 'u' to avoid conflict with AuthContext user
                <tr key={u.id_usuario}>
                  <td className="px-6 py-4 text-sm">{u.nome}</td>
                  <td className="px-6 py-4 text-sm">{u.email}</td>
                  <td className="px-6 py-4 text-sm capitalize">{u.papel}</td>
                  <td className="px-6 py-4 text-sm text-right space-x-2">
                    {isAdmin && ( // Only show edit/delete buttons if admin
                      <>
                        <button
                          onClick={() => handleEditClick(u)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => handleDelete(u.id_usuario)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Deletar
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Novo Usuário</h3>
            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <input
                type="text"
                placeholder="Nome"
                required
                value={formData.nome}
                onChange={(e) => setFormData({...formData, nome: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <input
                type="email"
                placeholder="Email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <input
                type="password"
                placeholder="Senha"
                required
                value={formData.senha}
                onChange={(e) => setFormData({...formData, senha: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <select
                value={formData.papel}
                onChange={(e) => setFormData({...formData, papel: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="visualizador">Visualizador</option>
                <option value="gestor">Gestor</option>
                <option value="admin">Admin</option>
              </select>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  Criar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Editar Usuário</h3>
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <input
                type="text"
                placeholder="Nome"
                required
                value={formData.nome}
                onChange={(e) => setFormData({...formData, nome: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <input
                type="email"
                placeholder="Email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <input
                type="password"
                placeholder="Nova Senha (deixe em branco para não alterar)"
                value={formData.senha}
                onChange={(e) => setFormData({...formData, senha: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <select
                value={formData.papel}
                onChange={(e) => setFormData({...formData, papel: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="visualizador">Visualizador</option>
                <option value="gestor">Gestor</option>
                <option value="admin">Admin</option>
              </select>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => { setShowEditModal(false); setEditingUser(null); setFormData({ nome: '', email: '', senha: '', papel: 'visualizador' }); }}
                  className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  Salvar Alterações
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
