import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getLeague, listMembers } from '../api/leagues';
import { getLeagueRanking } from '../api/rankings';
import { listMatches, listTeams, listPlayers } from '../api/matches';
import { listMyPredictions } from '../api/predictions';
import { listGroupPredictions, listAllGroupPredictions } from '../api/groupPredictions';
import { listMySpecialPredictions, listLeagueSpecialPredictions } from '../api/specialPredictions';
import type { League, LeagueMember, RankingEntry, Match, Team, Player, Prediction, GroupPrediction, SpecialPrediction, SpecialCategory } from '../api/types';
import MatchCard from '../components/MatchCard';
import GroupPredictionCard from '../components/GroupPredictionCard';
import SpecialPredictionCard from '../components/SpecialPredictionCard';

type Tab = 'jogos' | 'grupos' | 'especiais' | 'ranking' | 'membros';

export default function LeagueDetailPage() {
  const { leagueId } = useParams<{ leagueId: string }>();
  const { user } = useAuth();
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
  const [allGroupPredictions, setAllGroupPredictions] = useState<GroupPrediction[]>([]);
  const [allSpecialPredictions, setAllSpecialPredictions] = useState<SpecialPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('jogos');
  const [matchFilter, setMatchFilter] = useState<'upcoming' | 'all' | 'finished'>('upcoming');
  const tabsRef = useRef<HTMLDivElement>(null);

  const loadData = async () => {
    if (!leagueId) return;

    const [l, m, r, matchesData, teamsData, playersData, predsData, groupPredsData, specialPredsData, allGroupPredsData, allSpecialPredsData] = await Promise.all([
      getLeague(leagueId),
      listMembers(leagueId),
      getLeagueRanking(leagueId).catch(() => []),
      listMatches(),
      listTeams(),
      listPlayers().catch(() => []),
      listMyPredictions(leagueId),
      listGroupPredictions(leagueId).catch(() => []),
      listMySpecialPredictions(leagueId).catch(() => []),
      listAllGroupPredictions(leagueId).catch(() => []),
      listLeagueSpecialPredictions(leagueId).catch(() => []),
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
    setAllGroupPredictions(allGroupPredsData);
    setAllSpecialPredictions(allSpecialPredsData);
    setLoading(false);
  };

  useEffect(() => {
    setLoading(true);
    setTab('jogos');
    loadData();
  }, [leagueId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  if (!league) return <div className="p-4 text-center text-gray-500">Liga não encontrada.</div>;

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
    { category: 'best_gk', label: 'Melhor GR', description: 'Melhor guarda-redes do torneio', type: 'player' },
  ];

  const specialPredMap: Record<string, SpecialPrediction> = {};
  specialPredictions.forEach((sp) => { specialPredMap[sp.category] = sp; });

  const userNames: Record<string, string> = {};
  members.forEach((m) => { userNames[m.user_id] = m.user_name; });

  const tabs: { key: Tab; label: string }[] = [
    { key: 'jogos', label: 'Jogos' },
    { key: 'grupos', label: 'Grupos' },
    { key: 'especiais', label: 'Especiais' },
    { key: 'ranking', label: 'Ranking' },
    { key: 'membros', label: 'Membros' },
  ];

  return (
    <div className="max-w-2xl mx-auto px-4 py-3">
      {/* Header */}
      <div className="mb-3">
        <div className="flex justify-between items-start gap-2">
          <div className="min-w-0 flex-1">
            <h1 className="text-lg font-bold text-gray-800 leading-tight truncate">{league.name}</h1>
            <p className="text-gray-400 text-xs mt-0.5">{league.season} · {members.length} membros</p>
          </div>
          <div className="text-right shrink-0">
            <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-1 rounded-lg border border-emerald-200">
              {league.invite_code}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs — horizontally scrollable on mobile */}
      <div
        ref={tabsRef}
        className="flex gap-0 mb-4 border-b border-gray-200 overflow-x-auto scrollbar-hide -mx-4 px-4"
        style={{ WebkitOverflowScrolling: 'touch' }}
      >
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-3 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px shrink-0 ${
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
                    : 'bg-gray-100 text-gray-500 active:bg-gray-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {sortedDays.length > 0 ? (
            <div className="space-y-5">
              {sortedDays.map((day) => {
                const dayDate = new Date(day + 'T12:00:00');
                const isToday = day === now.toISOString().slice(0, 10);
                const dayLabel = isToday
                  ? 'Hoje'
                  : dayDate.toLocaleDateString('pt-PT', { weekday: 'long', day: 'numeric', month: 'long' });

                return (
                  <div key={day}>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{dayLabel}</h3>
                    <div className="space-y-2">
                      {matchesByDay[day].map((match) => (
                        <MatchCard
                          key={match.id}
                          match={match}
                          teams={teams}
                          prediction={predictions[match.id]}
                          leagueId={leagueId!}
                          userNames={userNames}
                          onPredictionSaved={loadData}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8 text-sm">Sem jogos para mostrar.</p>
          )}
        </>
      )}

      {tab === 'grupos' && (
        <>
          <p className="text-xs text-gray-500 mb-3">
            Prevê a classificação final de cada grupo. 1 ponto por posição acertada (máx. 4 por grupo).
          </p>
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2">
            {sortedGroups.map((g) => {
              const groupStarted = allMatches.some(
                (m) => m.group_letter === g && m.stage === 'group' && m.status !== 'scheduled'
              );
              const othersGroupPreds = allGroupPredictions.filter(
                (gp) => gp.group_letter === g && gp.user_id !== user?.id
              );
              return (
                <GroupPredictionCard
                  key={g}
                  groupLetter={g}
                  teams={groups[g]}
                  leagueId={leagueId!}
                  existing={groupPredMap[g] || null}
                  locked={groupStarted}
                  othersPredictions={othersGroupPreds}
                  userNames={userNames}
                  onSaved={loadData}
                />
              );
            })}
          </div>
        </>
      )}

      {tab === 'especiais' && (
        <>
          <p className="text-xs text-gray-500 mb-3">
            Previsões especiais valem 6 pontos cada. Data limite: <span className="font-semibold">18 de junho, 17:00</span>.
          </p>
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2">
            {specialCategories.map((cat) => {
              const othersSpecialPreds = allSpecialPredictions.filter(
                (sp) => sp.category === cat.category && sp.user_id !== user?.id
              );
              return (
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
                othersPredictions={othersSpecialPreds}
                userNames={userNames}
                onSaved={loadData}
              />
              );
            })}
          </div>
        </>
      )}

      {tab === 'ranking' && (
        <>
          {ranking.length === 0 ? (
            <p className="text-gray-400 text-center py-8 text-sm">Ainda não há pontuações.</p>
          ) : (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-3 py-2.5 text-left text-gray-500 font-medium text-xs">#</th>
                    <th className="px-3 py-2.5 text-left text-gray-500 font-medium text-xs">Nome</th>
                    <th className="px-3 py-2.5 text-right text-gray-500 font-medium text-xs">Total</th>
                    <th className="px-3 py-2.5 text-right text-gray-500 font-medium text-xs hidden sm:table-cell">Pts Jogos</th>
                    <th className="px-3 py-2.5 text-right text-gray-500 font-medium text-xs">Exatos</th>
                  </tr>
                </thead>
                <tbody>
                  {ranking.map((entry, i) => (
                    <tr key={entry.user_id} className={`border-t ${i < 3 ? 'bg-emerald-50/50' : ''}`}>
                      <td className="px-3 py-2.5 font-bold text-gray-700 text-sm">{entry.position}</td>
                      <td className="px-3 py-2.5 font-medium text-gray-800 text-sm">{entry.name}</td>
                      <td className="px-3 py-2.5 text-right font-bold text-emerald-600 text-sm">{entry.total_points}</td>
                      <td className="px-3 py-2.5 text-right text-gray-400 text-sm hidden sm:table-cell">{entry.match_points}</td>
                      <td className="px-3 py-2.5 text-right text-gray-400 text-sm">{entry.exact_scores}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {tab === 'membros' && (
        <div className="space-y-1.5">
          {members.map((member) => (
            <div key={member.id} className="bg-white border border-gray-200 rounded-lg px-3 py-2.5 flex justify-between items-center">
              <span className="text-sm text-gray-800">{member.user_name}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${
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
