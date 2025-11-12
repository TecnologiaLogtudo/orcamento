import { useState, useEffect } from 'react';
import { categoriasAPI } from '../services/api';
import { Plus, Edit, Trash2, Upload, Search } from 'lucide-react';

export default function Categorias() {
  const [categorias, setCategorias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCategoria, setEditingCategoria] = useState(null);
  const [search, setSearch] = useState('');
  const [formData, setFormData] = useState({
    categoria: '',
    uf: '',
    master: '',
    grupo: '',
    cod_class: '',
    classe_custo: ''
  });

  useEffect(() => {
    loadCategorias();
  }, [search]);

  const loadCategorias = async () => {
    try {
      setLoading(true);
      const data = await categoriasAPI.list({ search });
      setCategorias(data);
    } catch (error) {
      alert('Erro ao carregar categorias: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCategoria) {
        await categoriasAPI.update(editingCategoria.id_categoria, formData);
        alert('Categoria atualizada com sucesso!');
      } else {
        await categoriasAPI.create(formData);
        alert('Categoria criada com sucesso!');
      }
      setShowModal(false);
      resetForm();
      loadCategorias();
    } catch (error) {
      alert('Erro: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleEdit = (categoria) => {
    setEditingCategoria(categoria);
    setFormData({
      categoria: categoria.categoria,
      uf: categoria.uf || '',
      master: categoria.master || '',
      grupo: categoria.grupo || '',
      cod_class: categoria.cod_class || '',
      classe_custo: categoria.classe_custo || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja deletar esta categoria?')) return;
    
    try {
      await categoriasAPI.delete(id);
      alert('Categoria deletada com sucesso!');
      loadCategorias();
    } catch (error) {
      alert('Erro: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const result = await categoriasAPI.import(file);
      alert(`${result.imported} categorias importadas com sucesso!`);
      if (result.errors && result.errors.length > 0) {
        console.error('Erros na importação:', result.errors);
      }
      loadCategorias();
    } catch (error) {
      alert('Erro ao importar: ' + (error.response?.data?.error || error.message));
    }
    e.target.value = '';
  };

  const resetForm = () => {
    setFormData({
      categoria: '',
      uf: '',
      master: '',
      grupo: '',
      cod_class: '',
      classe_custo: ''
    });
    setEditingCategoria(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Categorias</h1>
            <p className="text-gray-600 mt-1">Gerencie as categorias orçamentárias</p>
          </div>

          <div className="flex flex-wrap gap-3">
            <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
              <Upload size={20} />
              Importar Excel
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleImport}
                className="hidden"
              />
            </label>

            <button
              onClick={() => {
                resetForm();
                setShowModal(true);
              }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
            >
              <Plus size={20} />
              Nova Categoria
            </button>
          </div>
        </div>

        {/* Busca */}
        <div className="mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Buscar por categoria, grupo ou classe..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoria</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">UF</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grupo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cód. Classe</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Classe Custo</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {categorias.map((categoria) => (
                  <tr key={categoria.id_categoria} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{categoria.categoria}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{categoria.uf || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{categoria.grupo || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{categoria.cod_class || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{categoria.classe_custo || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleEdit(categoria)}
                        className="text-indigo-600 hover:text-indigo-900 mr-3"
                      >
                        <Edit size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(categoria.id_categoria)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {categorias.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500">Nenhuma categoria encontrada</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
          <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                {editingCategoria ? 'Editar Categoria' : 'Nova Categoria'}
              </h3>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Categoria *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.categoria}
                      onChange={(e) => setFormData({...formData, categoria: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">UF</label>
                    <input
                      type="text"
                      value={formData.uf}
                      onChange={(e) => setFormData({...formData, uf: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Centro de custo</label>
                    <input
                      type="text"
                      value={formData.master}
                      onChange={(e) => setFormData({...formData, master: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Grupo</label>
                    <input
                      type="text"
                      value={formData.grupo}
                      onChange={(e) => setFormData({...formData, grupo: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Cód. Classe</label>
                    <input
                      type="text"
                      value={formData.cod_class}
                      onChange={(e) => setFormData({...formData, cod_class: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Classe Custo</label>
                  <input
                    type="text"
                    value={formData.classe_custo}
                    onChange={(e) => setFormData({...formData, classe_custo: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                <div className="flex justify-end gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      resetForm();
                    }}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                  >
                    {editingCategoria ? 'Atualizar' : 'Criar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}