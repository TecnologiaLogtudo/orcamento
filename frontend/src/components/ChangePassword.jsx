import { useState } from 'react';
import { authAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function ChangePassword() {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');

    if (newPassword !== confirmNewPassword) {
      setError('A nova senha e a confirmação da nova senha não coincidem.');
      return;
    }

    if (newPassword.length < 6) { // Example: minimum password length
        setError('A nova senha deve ter pelo menos 6 caracteres.');
        return;
    }

    try {
      await authAPI.changePassword(oldPassword, newPassword);
      setMessage('Senha alterada com sucesso!');
      setOldPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
      // Optionally redirect after a delay or show a persistent message
      setTimeout(() => navigate('/dashboard'), 2000); // Redirect to dashboard after 2 seconds
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao alterar a senha.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 p-10 bg-white rounded-xl shadow-lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Alterar Senha
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="old-password" className="sr-only">Senha Antiga</label>
              <input
                id="old-password"
                name="old-password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Senha Antiga"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="new-password" className="sr-only">Nova Senha</label>
              <input
                id="new-password"
                name="new-password"
                type="password"
                autoComplete="new-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Nova Senha"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="confirm-new-password" className="sr-only">Confirmar Nova Senha</label>
              <input
                id="confirm-new-password"
                name="confirm-new-password"
                type="password"
                autoComplete="new-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Confirmar Nova Senha"
                value={confirmNewPassword}
                onChange={(e) => setConfirmNewPassword(e.target.value)}
              />
            </div>
          </div>

          {message && <p className="mt-2 text-center text-sm text-green-600">{message}</p>}
          {error && <p className="mt-2 text-center text-sm text-red-600">{error}</p>}

          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Alterar Senha
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
