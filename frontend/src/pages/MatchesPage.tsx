import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { listMatches, listTeams } from '../api/matches';
import { listMyPredictions } from '../api/predictions';
import type { Match, Team, Prediction } from '../api/types';
import MatchCard from '../components/MatchCard';

type StageFilter = 'all' | 'group' | 'knockout';

export default function MatchesPage() {
  const [searchParams] = useSearchParams();
  const leagueId = searchParams.get('league') ?? '';

  const [matches, setMatches] = useState<Match[]>([]);
  const [teams, setTeams] = useState<Record<string, Team>>({});
  const [predictions, setPredictions] = useState<Record<string, Prediction>>({});
  const [filter, setFilter] = useState<StageFilter>('all');
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    const [matchesData, teamsData, predsData] = await Promise.all([
      listMatches(),
      listTeams(),
      leagueId ? listMyPredictions(leagueId) : Promise.resolve([]),
    ]);

    setMatches(matchesData.sort((a, b) => a.match_number - b.match_number));

    const teamMap: Record<string, Team> = {};
    teamsData.forEach((t) => { teamMap[t.id] = t; });
    setTeams(teamMap);

    const predMap: Record<string, Prediction> = {};
    predsData.forEach((p) => { predMap[p.match_id] = p; });
    setPredictions(predMap);

    setLoading(false);
  };

  useEffect(() => { loadData(); }, [leagueId]);

  const filtered = matches.filter((m) => {
    if (filter === 'group') return m.stage === 'group';
    if (filter === 'knockout') return m.stage !== 'group';
    return true;
  });

  if (loading) return <div className="p-8 text-center">A carregar jogos...</div>;

  if (!leagueId) {
    return (
      <div className="max-w-2xl mx-auto p-6 text-center">
        <p className="text-gray-500">Seleciona uma liga primeiro para submeter previsoes.</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Jogos</h1>

      <div className="flex gap-2 mb-6">
        {(['all', 'group', 'knockout'] as StageFilter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-sm ${
              filter === f ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            {f === 'all' ? 'Todos' : f === 'group' ? 'Fase de Grupos' : 'Eliminatorias'}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {filtered.map((match) => (
          <MatchCard
            key={match.id}
            match={match}
            teams={teams}
            prediction={predictions[match.id]}
            leagueId={leagueId}
            onPredictionSaved={loadData}
          />
        ))}
      </div>
    </div>
  );
}
