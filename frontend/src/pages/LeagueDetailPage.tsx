import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getLeague, listMembers } from '../api/leagues';
import { getLeagueRanking } from '../api/rankings';
import { listMatches, listTeams, listPlayers } from '../api/matches';
import { listMyPredictions } from '../api/predictions';
import { listGroupPredictions } from '../api/groupPredictions';
import { listMySpecialPredictions } from '../api/specialPredictions';
import type { League, LeagueMember, RankingEntry, Match, Team, Player, Prediction, GroupPrediction, SpecialPrediction, SpecialCategory } from '../api/types';
import MatchCard from '../components/MatchCard';
import GroupPredictionCard from '../components/GroupPredictionCard';
import SpecialPredictionCard from '../components/SpecialPredictionCard';

type Tab = 'jogos' | 'grupos' | 'especiais' | 'ranking' | 'membros';

export default function LeagueDetailPage() {
  const { leagueId } = useParams<{ leagueId: string }>();
  const [league, setLeague] = useState<League | null>(null);
  const [members, setMembers] = useState<LeagueMember[]>([]);
  const [ranking, setRanking] = useState<RankingEntry[]>([]);
  const [allMatches, setAllMatches] = useState<Match[]>([]);
  const [teams, setTeams] = useState<Record<string, Team>>({});
  const [teamsList, setTeamsList] = useState<Team[]>([]);
  const [predictions, setPredictions] = useState<Record<string, Prediction>>({});
  const [groupPredictions, setGroupPredictions] = useState<GroupPrediction[]>([]);
  const [allPlayers, setAllPlayers] = useState<Player[]>([]);
  const [specialPredictions, setSpecialPredictions] = useState<SpecialPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('jogos');
  const [matchFilter, setMatchFilter] = useState<'upcoming' | 'all' | 'finished'>('upcoming');

  const loadData = async () => {
    if (!leagueId) return;

    const [l, m, r, matchesData, teamsData, playersData, predsData, groupPredsData, specialPredsData] = await Promise.all([
      getLeague(leagueId),
      listMembers(leagueId),
      getLeagueRanking(leagueId).catch(() => []),
      listMatches(),
      listTeams(),
      listPlayers().catch(() => []),
      listMyPredictions(leagueId),
      listGroupPredictions(leagueId).catch(() => []),
      listMySpecialPredictions(leagueId).catch(() => []),
    ]);

    setLeague(l);
    setMembers(m);
    setRanking(r);

    const teamMap: Record<string, Team> = {};
    teamsData.forEach((t) => { teamMap[t.id] = t; });
    setTeams(teamMap);
    setTeamsList(teamsData);

    const predMap: Record<string, Prediction> = {};
    predsData.forEach((p) => { predMap[p.match_id] = p; });
    setPredictions(predMap);

    setAllMatches(matchesData.sort((a, b) => a.match_number - b.match_number));
    setAllPlayers(playersData);
    setGroupPredictions(groupPredsData);
    setSpecialPredictions(specialPredsData);
    setLoading(false);
  };

  useEffect(() => { loadData(); }, [leagueId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  if (!league) return <div className="p-8 text-center text-gray-500">Liga não encontrada.</div>;

  const now = new Date();
  const filteredMatches = allMatches.filter((m) => {
    if (matchFilter === 'upcoming') return m.status !== 'finished';
    if (matchFilter === 'finished') return m.status === 'finished';
    return true;
  });

  const matchesByDay = filteredMatches.reduce<Record<string, Match[]>>((acc, m) => {
    const day = m.match_date.slice(0, 10);
    if (!acc[day]) acc[day] = [];
    acc[day].push(m);
    return acc;
  }, {});

  const sortedDays = Object.keys(matchesByDay).sort();

  // Build groups from teams
  const groups = teamsList.reduce<Record<string, Team[]>>((acc, t) => {
    if (t.group_letter) {
      if (!acc[t.group_letter]) acc[t.group_letter] = [];
      acc[t.group_letter].push(t);
    }
    return acc;
  }, {});
  const sortedGroups = Object.keys(groups).sort();

  const groupPredMap: Record<string, GroupPrediction> = {};
  groupPredictions.forEach((gp) => { groupPredMap[gp.group_letter] = gp; });

  const specialCategories: { category: SpecialCategory; label: string; description: string; type: 'team' | 'player' }[] = [
    { category: 'champion', label: 'Campeão', description: 'Quem vai ganhar o Mundial?', type: 'team' },
    { category: 'mvp', label: 'MVP', description: 'Melhor jogador do torneio', type: 'player' },
    { category: 'golden_boot', label: 'Bota de Ouro', description: 'Melhor marcador do torneio', type: 'player' },
    { category: 'young_player', label: 'Melhor Jovem', description: 'Melhor jogador jovem do torneio', type: 'player' },
    { category: 'best_gk', label: 'Melhor Guarda-Redes', description: 'Melhor guarda-redes do torneio', type: 'player' },
  ];

  const specialPredMap: Record<string, SpecialPrediction> = {};
  specialPredictions.forEach((sp) => { specialPredMap[sp.category] = sp; });

  const tabs: { key: Tab; label: string }[] = [
    { key: 'jogos', label: 'Jogos' },
    { key: 'grupos', label: 'Grupos' },
    { key: 'especiais', label: 'Especiais' },
    { key: 'ranking', label: 'Ranking' },
    { key: 'membros', label: 'Membros' },
  ];

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 mb-1">{league.name}</h1>
            <p className="text-gray-400 text-sm">Temporada {league.season} · {members.length} membros</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-400 mb-1">Código de convite</p>
            <span className="text-sm font-mono font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-lg border border-emerald-200">
              {league.invite_code}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
              tab === t.key
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-gray-400 hover:text-gray-600'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'jogos' && (
        <>
          <div className="flex gap-1 mb-4">
            {([['upcoming', 'Próximos'], ['finished', 'Terminados'], ['all', 'Todos']] as const).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setMatchFilter(key)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                  matchFilter === key
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {sortedDays.length > 0 ? (
            <div className="space-y-6">
              {sortedDays.map((day) => {
                const dayDate = new Date(day + 'T12:00:00');
                const isToday = day === now.toISOString().slice(0, 10);
                const dayLabel = isToday
                  ? 'Hoje'
                  : dayDate.toLocaleDateString('pt-PT', { weekday: 'long', day: 'numeric', month: 'long' });

                return (
                  <div key={day}>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">{dayLabel}</h3>
                    <div className="space-y-3">
                      {matchesByDay[day].map((match) => (
                        <MatchCard
                          key={match.id}
                          match={match}
                          teams={teams}
                          prediction={predictions[match.id]}
                          leagueId={leagueId!}
                          onPredictionSaved={loadData}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">Sem jogos para mostrar.</p>
          )}
        </>
      )}

      {tab === 'grupos' && (
        <>
          <p className="text-sm text-gray-500 mb-4">
            Prevê a classificação final de cada grupo. 1 ponto por posição acertada (máx. 4 por grupo).
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {sortedGroups.map((g) => (
              <GroupPredictionCard
                key={g}
                groupLetter={g}
                teams={groups[g]}
                leagueId={leagueId!}
                existing={groupPredMap[g] || null}
                onSaved={loadData}
              />
            ))}
          </div>
        </>
      )}

      {tab === 'especiais' && (
        <>
          <p className="text-sm text-gray-500 mb-4">
            Previsões especiais valem 6 pontos cada. Podes alterar até ao final da fase de grupos.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {specialCategories.map((cat) => (
              <SpecialPredictionCard
                key={cat.category}
                category={cat.category}
                label={cat.label}
                description={cat.description}
                type={cat.type}
                teams={teamsList}
                players={allPlayers}
                leagueId={leagueId!}
                existing={specialPredMap[cat.category] || null}
                onSaved={loadData}
              />
            ))}
          </div>
        </>
      )}

      {tab === 'ranking' && (
        <>
          {ranking.length === 0 ? (
            <p className="text-gray-400 text-center py-8">Ainda não há pontuações.</p>
          ) : (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left text-gray-500 font-medium">#</th>
                    <th className="px-4 py-3 text-left text-gray-500 font-medium">Nome</th>
                    <th className="px-4 py-3 text-right text-gray-500 font-medium">Total</th>
                    <th className="px-4 py-3 text-right text-gray-500 font-medium hidden sm:table-cell">Jogos</th>
                    <th className="px-4 py-3 text-right text-gray-500 font-medium">Exatos</th>
                  </tr>
                </thead>
                <tbody>
                  {ranking.map((entry, i) => (
                    <tr key={entry.user_id} className={`border-t ${i < 3 ? 'bg-emerald-50/50' : ''}`}>
                      <td className="px-4 py-3 font-bold text-gray-700">{entry.position}</td>
                      <td className="px-4 py-3 font-medium text-gray-800">{entry.name}</td>
                      <td className="px-4 py-3 text-right font-bold text-emerald-600">{entry.total_points}</td>
                      <td className="px-4 py-3 text-right text-gray-400 hidden sm:table-cell">{entry.match_points}</td>
                      <td className="px-4 py-3 text-right text-gray-400">{entry.exact_scores}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {tab === 'membros' && (
        <div className="space-y-2">
          {members.map((member) => (
            <div key={member.id} className="bg-white border border-gray-200 rounded-lg px-4 py-3 flex justify-between items-center">
              <span className="text-sm text-gray-800">{member.user_name}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                member.role === 'admin'
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                {member.role === 'admin' ? 'Admin' : 'Participante'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
