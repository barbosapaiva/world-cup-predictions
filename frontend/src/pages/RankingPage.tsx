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
      <div className="max-w-2xl mx-auto px-4 text-center py-16">
        <p className="text-gray-400 text-sm">Seleciona uma liga para ver o ranking.</p>
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
    <div className="max-w-2xl mx-auto px-4 py-3">
      <h1 className="text-xl font-bold text-gray-800 mb-4">Ranking</h1>

      {ranking.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 text-sm">Ainda não há pontuações.</p>
        </div>
      ) : (
        <>
          {/* Podium */}
          {ranking.length >= 3 && (
            <div className="flex justify-center items-end gap-3 mb-6">
              {[1, 0, 2].map((idx) => {
                const entry = ranking[idx];
                if (!entry) return null;
                const heights = ['h-24', 'h-16', 'h-12'];
                return (
                  <div key={entry.user_id} className="flex flex-col items-center">
                    <div className={`w-10 h-10 rounded-full ${podiumColors[idx]} flex items-center justify-center font-extrabold text-sm mb-1.5`}>
                      {idx + 1}
                    </div>
                    <p className="text-xs font-semibold text-gray-800 mb-0.5 text-center max-w-[80px] truncate">{entry.name}</p>
                    <p className="text-[10px] text-emerald-600 font-bold mb-1.5">{entry.total_points} pts</p>
                    <div className={`${heights[idx]} w-16 sm:w-20 ${podiumColors[idx]} rounded-t-lg opacity-30`} />
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
                  <th className="px-3 py-2.5 text-left text-gray-500 font-medium text-xs">#</th>
                  <th className="px-3 py-2.5 text-left text-gray-500 font-medium text-xs">Nome</th>
                  <th className="px-3 py-2.5 text-right text-gray-500 font-medium text-xs">Total</th>
                  <th className="px-3 py-2.5 text-right text-gray-500 font-medium text-xs hidden sm:table-cell">Jogos</th>
                  <th className="px-3 py-2.5 text-right text-gray-500 font-medium text-xs hidden sm:table-cell">Grupos</th>
                  <th className="px-3 py-2.5 text-right text-gray-500 font-medium text-xs hidden sm:table-cell">Especiais</th>
                  <th className="px-3 py-2.5 text-right text-gray-500 font-medium text-xs">Exatos</th>
                </tr>
              </thead>
              <tbody>
                {ranking.map((entry, i) => (
                  <tr
                    key={entry.user_id}
                    className={`border-t ${i < 3 ? 'bg-emerald-50/50' : ''}`}
                  >
                    <td className="px-3 py-2.5 font-bold text-gray-700">{entry.position}</td>
                    <td className="px-3 py-2.5 font-medium text-gray-800">{entry.name}</td>
                    <td className="px-3 py-2.5 text-right font-bold text-emerald-600">{entry.total_points}</td>
                    <td className="px-3 py-2.5 text-right text-gray-400 hidden sm:table-cell">{entry.match_points}</td>
                    <td className="px-3 py-2.5 text-right text-gray-400 hidden sm:table-cell">{entry.group_prediction_points}</td>
                    <td className="px-3 py-2.5 text-right text-gray-400 hidden sm:table-cell">{entry.special_prediction_points}</td>
                    <td className="px-3 py-2.5 text-right text-gray-400">{entry.exact_scores}</td>
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
