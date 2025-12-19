import { useState, useEffect } from 'react';
import { usuariosAPI } from '../services/api';

export default function UserEditModal({ user, onClose, onSave }) {
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    senha: '',
    papel: 'visualizador',
  });

  useEffect(() => {
    if (user) {
      setFormData({
        nome: user.nome,
        email: user.email,
        senha: '',
        papel: user.papel,
      });
    }
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToUpdate = { ...formData };
      if (!dataToUpdate.senha) {
        delete dataToUpdate.senha; // Não envia a senha se estiver vazia
      }
      await onSave(user.id_usuario, dataToUpdate);
    } catch (error) {
      // O erro já é tratado na função onSave, mas pode adicionar logs aqui se necessário
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-xl font-bold mb-4">Editar Usuário</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Nome"
            required
            value={formData.nome}
            onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
          <input
            type="email"
            placeholder="Email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
          <input
            type="password"
            placeholder="Nova Senha (deixe em branco para não alterar)"
            value={formData.senha}
            onChange={(e) => setFormData({ ...formData, senha: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
          <select
            value={formData.papel}
            onChange={(e) => setFormData({ ...formData, papel: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          >
            <option value="visualizador">Visualizador</option>
            <option value="gestor">Gestor</option>
            <option value="admin">Admin</option>
          </select>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
