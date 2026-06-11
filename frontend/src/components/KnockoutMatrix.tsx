import type { Match, Team } from '../api/types';

interface Props {
  matches: Match[];
  teams: Record<string, Team>;
}

// Official FIFA 2026 R32 bracket matrix
const BRACKET_MATRIX: [string, string][] = [
  ['1E', '3ABCDF'], ['1I', '3CDFGH'], ['2A', '2B'], ['1F', '2C'],
  ['2K', '2L'], ['1H', '2J'], ['1D', '3BEFIJ'], ['1G', '3AEHIJ'],
  ['1C', '2F'], ['2E', '2I'], ['1A', '3CEFHI'], ['1L', '3EHIJK'],
  ['1J', '2H'], ['2D', '2G'], ['1B', '3EFGLI'], ['1K', '3DEIJL'],
];

function formatSlot(slot: string): { label: string; isWildcard: boolean } {
  if (slot.startsWith('3')) {
    return { label: '3.º*', isWildcard: true };
  }
  const pos = slot[0] === '1' ? '1.º' : '2.º';
  const group = slot[1];
  return { label: `${pos} Grupo ${group}`, isWildcard: false };
}

export default function KnockoutMatrix({ matches, teams }: Props) {
  const r32 = matches
    .filter((m) => m.stage === 'R32')
    .sort((a, b) => a.match_number - b.match_number);

  // Try to resolve team names from actual R32 matches
  const resolvedTeams: Record<number, { home: string | null; away: string | null; homeFlag: string | null; awayFlag: string | null }> = {};
  r32.forEach((m, i) => {
    const homeTeam = m.home_team_id ? teams[m.home_team_id] : null;
    const awayTeam = m.away_team_id ? teams[m.away_team_id] : null;
    resolvedTeams[i] = {
      home: homeTeam?.code ?? null,
      away: awayTeam?.code ?? null,
      homeFlag: homeTeam?.flag_url ?? null,
      awayFlag: awayTeam?.flag_url ?? null,
    };
  });

  // Left bracket (matches 0-7), Right bracket (matches 8-15)
  const leftMatches = BRACKET_MATRIX.slice(0, 8);
  const rightMatches = BRACKET_MATRIX.slice(8, 16);

  const renderMatch = (pair: [string, string], idx: number, side: 'left' | 'right') => {
    const globalIdx = side === 'left' ? idx : idx + 8;
    const home = formatSlot(pair[0]);
    const away = formatSlot(pair[1]);
    const resolved = resolvedTeams[globalIdx];

    return (
      <div key={globalIdx} className="flex items-center bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs gap-2">
        {/* Home */}
        <div className="flex items-center gap-1.5 flex-1 min-w-0">
          {resolved?.homeFlag && <img src={resolved.homeFlag} alt="" className="w-5 h-3.5 object-cover rounded-sm flex-shrink-0" />}
          {resolved?.home ? (
            <span className="font-bold text-gray-800">{resolved.home}</span>
          ) : (
            <span className={`font-medium ${home.isWildcard ? 'text-amber-600' : 'text-emerald-700'}`}>
              {home.label}
            </span>
          )}
        </div>

        <span className="text-gray-300 font-bold text-[10px]">vs</span>

        {/* Away */}
        <div className="flex items-center gap-1.5 flex-1 min-w-0 justify-end">
          {resolved?.away ? (
            <span className="font-bold text-gray-800">{resolved.away}</span>
          ) : (
            <span className={`font-medium ${away.isWildcard ? 'text-amber-600' : 'text-emerald-700'}`}>
              {away.label}
            </span>
          )}
          {resolved?.awayFlag && <img src={resolved.awayFlag} alt="" className="w-5 h-3.5 object-cover rounded-sm flex-shrink-0" />}
        </div>
      </div>
    );
  };

  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
        Enquadramento — 16 Avos de Final (R32)
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Left bracket */}
        <div>
          <p className="text-xs font-semibold text-gray-400 mb-2 text-center">Lado Esquerdo</p>
          <div className="space-y-1.5">
            {leftMatches.map((pair, i) => renderMatch(pair, i, 'left'))}
          </div>
        </div>
        {/* Right bracket */}
        <div>
          <p className="text-xs font-semibold text-gray-400 mb-2 text-center">Lado Direito</p>
          <div className="space-y-1.5">
            {rightMatches.map((pair, i) => renderMatch(pair, i, 'right'))}
          </div>
        </div>
      </div>
      <p className="text-[10px] text-gray-400 mt-2">
        * 3.º = melhor 3.º classificado (wildcard). A atribuição exata depende de quais grupos apuram os 3.ºs.
      </p>
    </div>
  );
}
