import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getLeagueRanking } from '../api/rankings';
import { useLeague } from '../context/LeagueContext';
import type { RankingEntry } from '../api/types';

export default function RankingPage() {
  const [searchParams] = useSearchParams();
  const { activeLeague } = useLeague();
  const leagueId = searchParams.get('league') ?? activeLeague?.id ?? '';
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
    return (
      <div className="max-w-2xl mx-auto p-6 text-center py-16">
        <p className="text-gray-400 text-lg">Seleciona uma liga para ver o ranking.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  const podiumColors = [
    'bg-yellow-400 text-yellow-900',
    'bg-gray-300 text-gray-700',
    'bg-amber-600 text-amber-100',
  ];

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Ranking</h1>

      {ranking.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 text-lg">Ainda não há pontuações.</p>
        </div>
      ) : (
        <>
          {/* Podium */}
          {ranking.length >= 3 && (
            <div className="flex justify-center items-end gap-4 mb-8">
              {[1, 0, 2].map((idx) => {
                const entry = ranking[idx];
                if (!entry) return null;
                const heights = ['h-28', 'h-20', 'h-16'];
                return (
                  <div key={entry.user_id} className="flex flex-col items-center">
                    <div className={`w-12 h-12 rounded-full ${podiumColors[idx]} flex items-center justify-center font-extrabold text-lg mb-2`}>
                      {idx + 1}
                    </div>
                    <p className="text-sm font-semibold text-gray-800 mb-1">{entry.name}</p>
                    <p className="text-xs text-emerald-600 font-bold mb-2">{entry.total_points} pts</p>
                    <div className={`${heights[idx]} w-20 ${podiumColors[idx]} rounded-t-lg opacity-30`} />
                  </div>
                );
              })}
            </div>
          )}

          {/* Full table */}
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left text-gray-500 font-medium">#</th>
                  <th className="px-4 py-3 text-left text-gray-500 font-medium">Nome</th>
                  <th className="px-4 py-3 text-right text-gray-500 font-medium">Total</th>
                  <th className="px-4 py-3 text-right text-gray-500 font-medium hidden sm:table-cell">Jogos</th>
                  <th className="px-4 py-3 text-right text-gray-500 font-medium hidden sm:table-cell">Especiais</th>
                  <th className="px-4 py-3 text-right text-gray-500 font-medium">Exatos</th>
                </tr>
              </thead>
              <tbody>
                {ranking.map((entry, i) => (
                  <tr
                    key={entry.user_id}
                    className={`border-t ${i < 3 ? 'bg-emerald-50/50' : ''}`}
                  >
                    <td className="px-4 py-3 font-bold text-gray-700">{entry.position}</td>
                    <td className="px-4 py-3 font-medium text-gray-800">{entry.name}</td>
                    <td className="px-4 py-3 text-right font-bold text-emerald-600">{entry.total_points}</td>
                    <td className="px-4 py-3 text-right text-gray-400 hidden sm:table-cell">{entry.match_points}</td>
                    <td className="px-4 py-3 text-right text-gray-400 hidden sm:table-cell">{entry.special_prediction_points}</td>
                    <td className="px-4 py-3 text-right text-gray-400">{entry.exact_scores}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
