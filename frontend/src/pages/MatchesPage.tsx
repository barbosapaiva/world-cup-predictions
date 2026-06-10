import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { listMatches, listTeams } from '../api/matches';
import { listMyPredictions } from '../api/predictions';
import type { Match, Team, Prediction } from '../api/types';
import MatchCard from '../components/MatchCard';
import BracketView from '../components/BracketView';
import { useLeague } from '../context/LeagueContext';

type ViewMode = 'list' | 'bracket';
type StageFilter = 'all' | 'group' | 'knockout';

function formatDayHeader(dateStr: string): string {
  const date = new Date(dateStr);
  const today = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(today.getDate() + 1);

  const toDay = (d: Date) => d.toISOString().slice(0, 10);

  if (toDay(date) === toDay(today)) return 'Hoje';
  if (toDay(date) === toDay(tomorrow)) return 'Amanhã';

  return date.toLocaleDateString('pt-PT', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });
}

export default function MatchesPage() {
  const [searchParams] = useSearchParams();
  const { activeLeague } = useLeague();
  const leagueId = searchParams.get('league') ?? activeLeague?.id ?? '';

  const [matches, setMatches] = useState<Match[]>([]);
  const [teams, setTeams] = useState<Record<string, Team>>({});
  const [predictions, setPredictions] = useState<Record<string, Prediction>>({});
  const [filter, setFilter] = useState<StageFilter>('all');
  const [view, setView] = useState<ViewMode>('list');
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

  const filtered = useMemo(() => {
    return matches.filter((m) => {
      if (filter === 'group') return m.stage === 'group';
      if (filter === 'knockout') return m.stage !== 'group';
      return true;
    });
  }, [matches, filter]);

  // Group by day
  const groupedByDay = useMemo(() => {
    const groups: { date: string; label: string; matches: Match[] }[] = [];
    const dateMap = new Map<string, Match[]>();

    for (const m of filtered) {
      const day = m.match_date.slice(0, 10);
      if (!dateMap.has(day)) dateMap.set(day, []);
      dateMap.get(day)!.push(m);
    }

    const sortedDays = [...dateMap.keys()].sort();
    for (const day of sortedDays) {
      groups.push({
        date: day,
        label: formatDayHeader(day),
        matches: dateMap.get(day)!.sort((a, b) => a.match_number - b.match_number),
      });
    }

    return groups;
  }, [filtered]);

  const knockoutMatches = matches.filter((m) => m.stage !== 'group');

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  if (!leagueId) {
    return (
      <div className="max-w-2xl mx-auto p-6 text-center py-16">
        <p className="text-gray-400 text-lg">Seleciona uma liga primeiro para submeter previsões.</p>
      </div>
    );
  }

  return (
    <div className={view === 'bracket' ? 'p-6' : 'max-w-2xl mx-auto p-6'}>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-800">Jogos</h1>

        <div className="flex gap-2">
          <button
            onClick={() => setView('list')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              view === 'list'
                ? 'bg-emerald-600 text-white'
                : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            Lista
          </button>
          <button
            onClick={() => setView('bracket')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              view === 'bracket'
                ? 'bg-emerald-600 text-white'
                : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            Quadro
          </button>
        </div>
      </div>

      {view === 'bracket' ? (
        <BracketView matches={knockoutMatches} teams={teams} />
      ) : (
        <>
          <div className="flex gap-2 mb-6">
            {(['all', 'group', 'knockout'] as StageFilter[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === f
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {f === 'all' ? 'Todos' : f === 'group' ? 'Fase de Grupos' : 'Eliminatórias'}
              </button>
            ))}
          </div>

          <div className="space-y-8">
            {groupedByDay.map((group) => (
              <div key={group.date}>
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3 border-b border-gray-200 pb-2">
                  {group.label}
                </h2>
                <div className="space-y-3">
                  {group.matches.map((match) => (
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
            ))}
          </div>
        </>
      )}
    </div>
  );
}
