import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getLeague, listMembers } from '../api/leagues';
import { getLeagueRanking } from '../api/rankings';
import type { League, LeagueMember, RankingEntry } from '../api/types';

export default function LeagueDetailPage() {
  const { leagueId } = useParams<{ leagueId: string }>();
  const [league, setLeague] = useState<League | null>(null);
  const [members, setMembers] = useState<LeagueMember[]>([]);
  const [ranking, setRanking] = useState<RankingEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!leagueId) return;
    Promise.all([
      getLeague(leagueId),
      listMembers(leagueId),
      getLeagueRanking(leagueId).catch(() => []),
    ]).then(([l, m, r]) => {
      setLeague(l);
      setMembers(m);
      setRanking(r);
    }).finally(() => setLoading(false));
  }, [leagueId]);

  if (loading) return <div className="p-8 text-center">A carregar...</div>;
  if (!league) return <div className="p-8 text-center">Liga nao encontrada</div>;

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-2">{league.name}</h1>
      <p className="text-gray-500 text-sm mb-6">Temporada: {league.season} &middot; {members.length} membros</p>

      <div className="flex gap-3 mb-8">
        <Link
          to={`/matches?league=${leagueId}`}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
        >
          Ver Jogos
        </Link>
      </div>

      {ranking.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Ranking</h2>
          <div className="bg-white border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">#</th>
                  <th className="px-4 py-2 text-left">Nome</th>
                  <th className="px-4 py-2 text-right">Pts</th>
                  <th className="px-4 py-2 text-right">Exatos</th>
                </tr>
              </thead>
              <tbody>
                {ranking.map((entry) => (
                  <tr key={entry.user_id} className="border-t">
                    <td className="px-4 py-2 font-medium">{entry.position}</td>
                    <td className="px-4 py-2">{entry.name}</td>
                    <td className="px-4 py-2 text-right font-semibold">{entry.total_points}</td>
                    <td className="px-4 py-2 text-right text-gray-500">{entry.exact_scores}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
