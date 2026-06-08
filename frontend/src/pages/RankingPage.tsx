import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getLeagueRanking } from '../api/rankings';
import type { RankingEntry } from '../api/types';

export default function RankingPage() {
  const [searchParams] = useSearchParams();
  const leagueId = searchParams.get('league') ?? '';
  const [ranking, setRanking] = useState<RankingEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!leagueId) { setLoading(false); return; }
    getLeagueRanking(leagueId)
      .then(setRanking)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [leagueId]);

  if (!leagueId) {
    return <div className="max-w-2xl mx-auto p-6 text-center text-gray-500">Seleciona uma liga para ver o ranking.</div>;
  }

  if (loading) return <div className="p-8 text-center">A carregar...</div>;

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Ranking</h1>

      {ranking.length === 0 ? (
        <p className="text-gray-500 text-center">Ainda nao ha pontuacoes.</p>
      ) : (
        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left">#</th>
                <th className="px-4 py-3 text-left">Nome</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3 text-right hidden sm:table-cell">Jogos</th>
                <th className="px-4 py-3 text-right hidden sm:table-cell">Especiais</th>
                <th className="px-4 py-3 text-right">Exatos</th>
              </tr>
            </thead>
            <tbody>
              {ranking.map((entry, i) => (
                <tr
                  key={entry.user_id}
                  className={`border-t ${i < 3 ? 'bg-yellow-50' : ''}`}
                >
                  <td className="px-4 py-3 font-bold">
                    {entry.position <= 3 ? ['', '1', '2', '3'][entry.position] : entry.position}
                  </td>
                  <td className="px-4 py-3 font-medium">{entry.name}</td>
                  <td className="px-4 py-3 text-right font-bold text-blue-600">{entry.total_points}</td>
                  <td className="px-4 py-3 text-right text-gray-500 hidden sm:table-cell">{entry.match_points}</td>
                  <td className="px-4 py-3 text-right text-gray-500 hidden sm:table-cell">{entry.special_prediction_points}</td>
                  <td className="px-4 py-3 text-right text-gray-500">{entry.exact_scores}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
