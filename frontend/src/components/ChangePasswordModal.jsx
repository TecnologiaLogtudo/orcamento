import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { usuariosAPI } from '../services/api';

export default function ChangePasswordModal({ onClose }) {
  const { user, login } = useAuth();
  const [formData, setFormData] = useState({
    senha_antiga: '',
    nova_senha: '',
    confirmar_senha: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (formData.nova_senha !== formData.confirmar_senha) {
      setError('A nova senha e a confirmação não correspondem.');
      return;
    }
    if (!formData.nova_senha) {
      setError('A nova senha não pode estar em branco.');
      return;
    }

    try {
      // 1. Altera a senha
      await usuariosAPI.update(user.id_usuario, {
        senha_antiga: formData.senha_antiga,
        senha: formData.nova_senha,
      });

      // 2. Realiza o login com a nova senha para obter um novo token
      const loginResult = await login(user.email, formData.nova_senha);

      if (loginResult.success) {
        setSuccess('Senha alterada com sucesso! A sessão foi atualizada.');
        setTimeout(() => {
          onClose();
        }, 2000);
      } else {
        setError('Senha alterada, mas falha ao renovar a sessão. Por favor, faça login novamente.');
      }

    } catch (err) {
      setError(err.response?.data?.error || 'Ocorreu um erro ao alterar a senha.');
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-xl font-bold mb-4">Alterar Senha</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            placeholder="Senha Antiga"
            required
            value={formData.senha_antiga}
            onChange={(e) => setFormData({ ...formData, senha_antiga: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
          <input
            type="password"
            placeholder="Nova Senha"
            required
            value={formData.nova_senha}
            onChange={(e) => setFormData({ ...formData, nova_senha: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
          <input
            type="password"
            placeholder="Confirmar Nova Senha"
            required
            value={formData.confirmar_senha}
            onChange={(e) => setFormData({ ...formData, confirmar_senha: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          />
          
          {error && <p className="text-red-500 text-sm">{error}</p>}
          {success && <p className="text-green-500 text-sm">{success}</p>}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
              disabled={!!success}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400"
              disabled={!!success}
            >
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
