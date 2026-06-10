import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listLeagues, createLeague, joinLeagueByCode } from '../api/leagues';
import type { League } from '../api/types';

export default function LeaguesPage() {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const [name, setName] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadLeagues = async () => {
    try {
      const data = await listLeagues();
      setLeagues(data);
    } catch {
      setError('Erro ao carregar ligas.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadLeagues(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await createLeague({ name, season: '2026' });
      setName('');
      setShowCreate(false);
      loadLeagues();
    } catch {
      setError('Erro ao criar liga.');
    }
  };

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await joinLeagueByCode(joinCode);
      setJoinCode('');
      setShowJoin(false);
      setSuccess('Entraste na liga!');
      loadLeagues();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (detail === 'Invalid invite code') {
        setError('Código inválido.');
      } else if (detail === 'Already a member of this league') {
        setError('Já estás nesta liga.');
      } else {
        setError('Erro ao entrar na liga.');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">As minhas Ligas</h1>
        <div className="flex gap-2">
          <button
            onClick={() => { setShowJoin(!showJoin); setShowCreate(false); }}
            className="bg-white border border-emerald-600 text-emerald-600 px-4 py-2 rounded-lg hover:bg-emerald-50 text-sm font-medium transition-colors"
          >
            Entrar com código
          </button>
          <button
            onClick={() => { setShowCreate(!showCreate); setShowJoin(false); }}
            className="bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 text-sm font-medium transition-colors"
          >
            + Criar Liga
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 p-3 rounded-lg mb-4 text-sm">
          {success}
        </div>
      )}

      {showJoin && (
        <form onSubmit={handleJoin} className="bg-white border border-gray-200 p-4 rounded-xl mb-6 shadow-sm">
          <p className="text-sm text-gray-500 mb-3">Introduz o código de convite da liga:</p>
          <div className="flex gap-3">
            <input
              type="text"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              placeholder="Ex: A1B2C3D4"
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono uppercase tracking-wider focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              required
            />
            <button type="submit" className="bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 text-sm font-medium transition-colors">
              Entrar
            </button>
          </div>
        </form>
      )}

      {showCreate && (
        <form onSubmit={handleCreate} className="bg-white border border-gray-200 p-4 rounded-xl mb-6 flex gap-3 shadow-sm">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Nome da liga"
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            required
          />
          <button type="submit" className="bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 text-sm font-medium transition-colors">
            Criar
          </button>
        </form>
      )}

      {leagues.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 text-lg mb-2">Nenhuma liga encontrada</p>
          <p className="text-gray-400 text-sm">Cria uma liga ou entra com um código de convite!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {leagues.map((league) => (
            <Link
              key={league.id}
              to={`/leagues/${league.id}`}
              className="block bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-center">
                <span className="font-semibold text-gray-800">{league.name}</span>
                <div className="flex gap-2 items-center">
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full font-mono">
                    {league.invite_code}
                  </span>
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">
                    {league.season}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
