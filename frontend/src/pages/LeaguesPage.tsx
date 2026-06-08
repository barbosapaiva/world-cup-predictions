import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listLeagues, createLeague, joinLeague } from '../api/leagues';
import { useAuth } from '../context/AuthContext';
import type { League } from '../api/types';

export default function LeaguesPage() {
  const { user } = useAuth();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadLeagues = async () => {
    try {
      const data = await listLeagues();
      setLeagues(data);
    } catch {
      setError('Erro ao carregar ligas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadLeagues(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createLeague({ name, season: '2026' });
      setName('');
      setShowCreate(false);
      loadLeagues();
    } catch {
      setError('Erro ao criar liga');
    }
  };

  const handleJoin = async (leagueId: string) => {
    if (!user) return;
    try {
      await joinLeague(leagueId, user.id);
      loadLeagues();
    } catch {
      setError('Erro ao entrar na liga');
    }
  };

  if (loading) return <div className="p-8 text-center">A carregar...</div>;

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Ligas</h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
        >
          + Criar Liga
        </button>
      </div>

      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm">{error}</div>}

      {showCreate && (
        <form onSubmit={handleCreate} className="bg-gray-50 p-4 rounded-lg mb-6 flex gap-3">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Nome da liga"
            className="flex-1 border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm">
            Criar
          </button>
        </form>
      )}

      {leagues.length === 0 ? (
        <p className="text-gray-500 text-center py-12">Nenhuma liga encontrada. Cria a primeira!</p>
      ) : (
        <div className="space-y-3">
          {leagues.map((league) => (
            <div key={league.id} className="bg-white border rounded-lg p-4 flex justify-between items-center">
              <Link to={`/leagues/${league.id}`} className="font-medium hover:text-blue-600">
                {league.name}
              </Link>
              <div className="flex gap-2 items-center">
                <span className="text-xs text-gray-400">{league.season}</span>
                <button
                  onClick={() => handleJoin(league.id)}
                  className="text-xs bg-gray-100 px-3 py-1 rounded hover:bg-gray-200"
                >
                  Entrar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
