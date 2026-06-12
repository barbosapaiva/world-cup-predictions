import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listLeagues, createLeague, joinLeagueByCode } from '../api/leagues';
import { useLeague } from '../context/LeagueContext';
import type { League } from '../api/types';

export default function LeaguesPage() {
  const { refreshLeagues: refreshLeagueContext } = useLeague();
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
      refreshLeagueContext();
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
      refreshLeagueContext();
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
    <div className="max-w-2xl mx-auto px-4 py-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold text-gray-800">As minhas Ligas</h1>
        <div className="flex gap-2">
          <button
            onClick={() => { setShowJoin(!showJoin); setShowCreate(false); }}
            className="bg-white border border-emerald-600 text-emerald-600 px-3 py-2 rounded-lg hover:bg-emerald-50 text-xs font-medium transition-colors"
          >
            Código
          </button>
          <button
            onClick={() => { setShowCreate(!showCreate); setShowJoin(false); }}
            className="bg-emerald-600 text-white px-3 py-2 rounded-lg hover:bg-emerald-700 text-xs font-medium transition-colors"
          >
            + Criar
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg mb-3 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 p-3 rounded-lg mb-3 text-sm">
          {success}
        </div>
      )}

      {showJoin && (
        <form onSubmit={handleJoin} className="bg-white border border-gray-200 p-4 rounded-xl mb-4 shadow-sm">
          <p className="text-sm text-gray-500 mb-3">Introduz o código de convite da liga:</p>
          <div className="flex gap-2">
            <input
              type="text"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              placeholder="Ex: A1B2C3D4"
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2.5 text-sm font-mono uppercase tracking-wider focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              required
            />
            <button type="submit" className="bg-emerald-600 text-white px-4 py-2.5 rounded-lg hover:bg-emerald-700 text-sm font-medium transition-colors">
              Entrar
            </button>
          </div>
        </form>
      )}

      {showCreate && (
        <form onSubmit={handleCreate} className="bg-white border border-gray-200 p-4 rounded-xl mb-4 flex gap-2 shadow-sm">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Nome da liga"
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            required
          />
          <button type="submit" className="bg-emerald-600 text-white px-4 py-2.5 rounded-lg hover:bg-emerald-700 text-sm font-medium transition-colors">
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
        <div className="space-y-2">
          {leagues.map((league) => (
            <Link
              key={league.id}
              to={`/leagues/${league.id}`}
              className="block bg-white border border-gray-200 rounded-xl p-4 shadow-sm active:bg-gray-50 transition-colors"
            >
              <div className="flex justify-between items-center">
                <span className="font-semibold text-gray-800 text-sm">{league.name}</span>
                <div className="flex gap-1.5 items-center">
                  <span className="text-[10px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full font-mono">
                    {league.invite_code}
                  </span>
                  <span className="text-[10px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
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
