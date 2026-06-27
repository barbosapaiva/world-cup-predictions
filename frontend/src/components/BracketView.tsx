import { useRef, useState, useEffect } from 'react';
import type { Match, Team } from '../api/types';

interface Props {
  matches: Match[];
  teams: Record<string, Team>;
}

const CARD_W = 180;
const CARD_H = 52;
const COL_GAP = 32;
const PAD = 16;

function getTeamName(match: Match, teams: Record<string, Team>, side: 'home' | 'away'): string {
  const teamId = side === 'home' ? match.home_team_id : match.away_team_id;
  const placeholder = side === 'home' ? match.home_placeholder : match.away_placeholder;
  if (teamId && teams[teamId]) return teams[teamId].name;
  return placeholder ?? 'TBD';
}

function getTeamFlag(match: Match, teams: Record<string, Team>, side: 'home' | 'away'): string | null {
  const teamId = side === 'home' ? match.home_team_id : match.away_team_id;
  if (teamId && teams[teamId]) return teams[teamId].flag_url;
  return null;
}

function isTBD(match: Match, side: 'home' | 'away'): boolean {
  const teamId = side === 'home' ? match.home_team_id : match.away_team_id;
  return !teamId;
}

function distributeY(count: number, totalHeight: number): number[] {
  if (count === 0) return [];
  if (count === 1) return [totalHeight / 2 - CARD_H / 2];
  const spacing = totalHeight / count;
  return Array.from({ length: count }, (_, i) => spacing * i + spacing / 2 - CARD_H / 2);
}

function TeamRow({
  name,
  flagUrl,
  score,
  isWinner,
  isFinished,
  isTop,
  isTbd,
  flip,
}: {
  name: string;
  flagUrl: string | null;
  score: number | null;
  isWinner: boolean;
  isFinished: boolean;
  isTop: boolean;
  isTbd: boolean;
  flip?: boolean;
}) {
  const displayName = name.length > 14 ? name.slice(0, 12) + '…' : name;
  const textColor = isTbd ? 'text-gray-300' : isWinner ? 'font-bold text-gray-900' : 'text-gray-600';
  const scoreColor = isWinner ? 'font-bold text-emerald-700' : 'text-gray-400';
  const bg = isWinner ? 'bg-emerald-50/70' : 'bg-white';

  return (
    <div
      className={`flex items-center gap-1.5 px-2 ${bg} ${
        isTop ? 'rounded-t-lg' : 'rounded-b-lg border-t border-gray-100'
      }`}
      style={{ width: CARD_W, height: CARD_H / 2 }}
    >
      {flip ? (
        <>
          <span className={`font-mono text-[11px] w-5 text-center ${scoreColor}`}>
            {isFinished ? score : '–'}
          </span>
          <div className="flex-1 flex items-center justify-end gap-1.5 min-w-0">
            <span className={`text-[11px] truncate ${textColor}`}>{displayName}</span>
            {flagUrl && <img src={flagUrl} alt="" className="w-5 h-3.5 object-cover rounded-sm shrink-0" />}
          </div>
        </>
      ) : (
        <>
          <div className="flex-1 flex items-center gap-1.5 min-w-0">
            {flagUrl && <img src={flagUrl} alt="" className="w-5 h-3.5 object-cover rounded-sm shrink-0" />}
            <span className={`text-[11px] truncate ${textColor}`}>{displayName}</span>
          </div>
          <span className={`font-mono text-[11px] w-5 text-center ${scoreColor}`}>
            {isFinished ? score : '–'}
          </span>
        </>
      )}
    </div>
  );
}

function BracketCard({
  match,
  teams,
  style,
  flip,
}: {
  match: Match;
  teams: Record<string, Team>;
  style: React.CSSProperties;
  flip?: boolean;
}) {
  const isFinished = match.status === 'finished';
  const homeWon = isFinished && (match.home_score ?? 0) > (match.away_score ?? 0);
  const awayWon = isFinished && (match.away_score ?? 0) > (match.home_score ?? 0);

  return (
    <div
      className="absolute border border-gray-200 rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow"
      style={{ ...style, width: CARD_W, height: CARD_H }}
    >
      <TeamRow
        name={getTeamName(match, teams, 'home')}
        flagUrl={getTeamFlag(match, teams, 'home')}
        score={match.home_score}
        isWinner={homeWon}
        isFinished={isFinished}
        isTop={true}
        isTbd={isTBD(match, 'home')}
        flip={flip}
      />
      <TeamRow
        name={getTeamName(match, teams, 'away')}
        flagUrl={getTeamFlag(match, teams, 'away')}
        score={match.away_score}
        isWinner={awayWon}
        isFinished={isFinished}
        isTop={false}
        isTbd={isTBD(match, 'away')}
        flip={flip}
      />
    </div>
  );
}

function ConnectorLines({
  positions,
  side,
}: {
  positions: { x: number; y: number }[][];
  side: 'left' | 'right';
}) {
  const paths: string[] = [];

  for (let col = 0; col < positions.length - 1; col++) {
    const curr = positions[col];
    const next = positions[col + 1];

    for (let i = 0; i < next.length; i++) {
      const s1 = curr[i * 2];
      const s2 = curr[i * 2 + 1];
      const target = next[i];
      if (!s1 || !target) continue;

      const s1Mid = s1.y + CARD_H / 2;
      const tMid = target.y + CARD_H / 2;

      if (side === 'left') {
        const exitX = s1.x + CARD_W;
        const enterX = target.x;
        const midX = exitX + (enterX - exitX) / 2;
        paths.push(`M ${exitX} ${s1Mid} H ${midX}`);
        paths.push(`M ${midX} ${s1Mid} V ${tMid}`);
        paths.push(`M ${midX} ${tMid} H ${enterX}`);
        if (s2) {
          const s2Mid = s2.y + CARD_H / 2;
          paths.push(`M ${exitX} ${s2Mid} H ${midX}`);
          paths.push(`M ${midX} ${s2Mid} V ${tMid}`);
        }
      } else {
        const exitX = s1.x;
        const enterX = target.x + CARD_W;
        const midX = exitX - (exitX - enterX) / 2;
        paths.push(`M ${exitX} ${s1Mid} H ${midX}`);
        paths.push(`M ${midX} ${s1Mid} V ${tMid}`);
        paths.push(`M ${midX} ${tMid} H ${enterX}`);
        if (s2) {
          const s2Mid = s2.y + CARD_H / 2;
          paths.push(`M ${exitX} ${s2Mid} H ${midX}`);
          paths.push(`M ${midX} ${s2Mid} V ${tMid}`);
        }
      }
    }
  }

  return (
    <>
      {paths.map((d, i) => (
        <path key={i} d={d} fill="none" stroke="#d1d5db" strokeWidth={1.5} />
      ))}
    </>
  );
}

export default function BracketView({ matches, teams }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  const getStageMatches = (stages: string[]) =>
    matches
      .filter((m) => stages.includes(m.stage))
      .sort((a, b) => a.match_number - b.match_number);

  // Separate R32 and R16 properly
  const r32 = getStageMatches(['R32']);
  const r16 = getStageMatches(['R16']);
  const qf = getStageMatches(['QF']);
  const sf = getStageMatches(['SF']);
  const final = getStageMatches(['F']);
  const thirdPlace = getStageMatches(['3rd']);

  // Split each round into left/right halves
  const half = <T,>(arr: T[]) => [arr.slice(0, Math.ceil(arr.length / 2)), arr.slice(Math.ceil(arr.length / 2))] as const;

  const [leftR32, rightR32] = half(r32);
  const [leftR16, rightR16] = half(r16);
  const [leftQF, rightQF] = half(qf);
  const [leftSF, rightSF] = half(sf);

  // Build round arrays per side (only include non-empty rounds)
  const leftRounds = [leftR32, leftR16, leftQF, leftSF].filter((r) => r.length > 0);
  const rightRounds = [rightR32, rightR16, rightQF, rightSF].filter((r) => r.length > 0);

  // Stage labels per column index
  const stageLabels = ['16 Avos', 'Oitavos', 'Quartos', 'Meias'];

  const HEADER_H = 50;
  const maxCards = Math.max(leftR32.length, rightR32.length, leftR16.length, rightR16.length, 1);
  const totalHeight = maxCards * CARD_H + (maxCards - 1) * 8;

  const leftCols = leftRounds.length;
  const rightCols = rightRounds.length;
  const maxCols = Math.max(leftCols, rightCols);
  const centerWidth = CARD_W + COL_GAP * 2;
  const sideWidth = maxCols * (CARD_W + COL_GAP);
  const totalWidth = sideWidth * 2 + centerWidth + PAD * 2;

  // Compute card positions
  const leftPositions: { x: number; y: number }[][] = [];
  for (let col = 0; col < leftRounds.length; col++) {
    const x = PAD + col * (CARD_W + COL_GAP);
    const ys = distributeY(leftRounds[col].length, totalHeight);
    leftPositions.push(ys.map((y) => ({ x, y: y + HEADER_H })));
  }

  const rightPositions: { x: number; y: number }[][] = [];
  for (let col = 0; col < rightRounds.length; col++) {
    const x = totalWidth - PAD - CARD_W - col * (CARD_W + COL_GAP);
    const ys = distributeY(rightRounds[col].length, totalHeight);
    rightPositions.push(ys.map((y) => ({ x, y: y + HEADER_H })));
  }

  const centerX = totalWidth / 2 - CARD_W / 2;
  const finalY = totalHeight / 2 - CARD_H / 2 + HEADER_H;

  // Connect last left column → final
  const leftToFinalPaths: string[] = [];
  if (leftPositions.length > 0) {
    const last = leftPositions[leftPositions.length - 1];
    for (const pos of last) {
      const ex = pos.x + CARD_W;
      const ey = pos.y + CARD_H / 2;
      const nx = centerX;
      const ny = finalY + CARD_H / 2;
      const mx = ex + (nx - ex) / 2;
      leftToFinalPaths.push(`M ${ex} ${ey} H ${mx}`, `M ${mx} ${ey} V ${ny}`, `M ${mx} ${ny} H ${nx}`);
    }
  }

  const rightToFinalPaths: string[] = [];
  if (rightPositions.length > 0) {
    const last = rightPositions[rightPositions.length - 1];
    for (const pos of last) {
      const ex = pos.x;
      const ey = pos.y + CARD_H / 2;
      const nx = centerX + CARD_W;
      const ny = finalY + CARD_H / 2;
      const mx = ex - (ex - nx) / 2;
      rightToFinalPaths.push(`M ${ex} ${ey} H ${mx}`, `M ${mx} ${ey} V ${ny}`, `M ${mx} ${ny} H ${nx}`);
    }
  }

  const svgHeight = totalHeight + HEADER_H + 20 + (thirdPlace.length > 0 ? CARD_H + 60 : 0);

  useEffect(() => {
    const update = () => {
      if (!containerRef.current) return;
      const parent = containerRef.current.parentElement;
      if (!parent) return;
      const availW = parent.clientWidth;
      const availH = window.innerHeight - containerRef.current.getBoundingClientRect().top - 16;
      const isMobile = availW < 640;
      if (isMobile) {
        setScale(Math.min(availH / svgHeight, 0.35));
      } else {
        setScale(Math.min(availW / totalWidth, availH / svgHeight, 1));
      }
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, [totalWidth, svgHeight]);

  const hasKnockout = r32.length > 0 || r16.length > 0 || qf.length > 0 || sf.length > 0 || final.length > 0;

  if (!hasKnockout) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-400 text-sm">Ainda não há jogos eliminatórios.</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="overflow-x-auto sm:overflow-hidden sm:flex sm:justify-center" style={{ height: svgHeight * scale }}>
      <div className="relative origin-top-left sm:origin-top" style={{ width: totalWidth * scale, height: svgHeight * scale }}>
        <div className="absolute top-0 left-0" style={{ width: totalWidth, height: svgHeight, transform: `scale(${scale})`, transformOrigin: 'top left' }}>

          {/* SVG connectors */}
          <svg className="absolute inset-0 pointer-events-none" width={totalWidth} height={svgHeight}>
            <ConnectorLines positions={leftPositions} side="left" />
            <ConnectorLines positions={rightPositions} side="right" />
            {leftToFinalPaths.map((d, i) => (
              <path key={`lf-${i}`} d={d} fill="none" stroke="#d1d5db" strokeWidth={1.5} />
            ))}
            {rightToFinalPaths.map((d, i) => (
              <path key={`rf-${i}`} d={d} fill="none" stroke="#d1d5db" strokeWidth={1.5} />
            ))}
          </svg>

          {/* Stage labels — left */}
          {leftRounds.map((_, col) => (
            <div
              key={`ll-${col}`}
              className="absolute text-[11px] font-semibold text-emerald-700 uppercase tracking-wide"
              style={{ left: PAD + col * (CARD_W + COL_GAP), top: 16, width: CARD_W, textAlign: 'center' }}
            >
              {stageLabels[col] ?? ''}
            </div>
          ))}

          {/* Final label */}
          {final.length > 0 && (
            <div
              className="absolute text-sm font-bold text-emerald-800 uppercase tracking-wide"
              style={{ left: centerX, top: 12, width: CARD_W, textAlign: 'center' }}
            >
              Final
            </div>
          )}

          {/* Stage labels — right */}
          {rightRounds.map((_, col) => (
            <div
              key={`rl-${col}`}
              className="absolute text-[11px] font-semibold text-emerald-700 uppercase tracking-wide"
              style={{ left: totalWidth - PAD - CARD_W - col * (CARD_W + COL_GAP), top: 16, width: CARD_W, textAlign: 'center' }}
            >
              {stageLabels[col] ?? ''}
            </div>
          ))}

          {/* Left match cards */}
          {leftRounds.map((round, col) =>
            round.map((match, idx) => (
              <BracketCard
                key={match.id}
                match={match}
                teams={teams}
                style={{ left: leftPositions[col][idx].x, top: leftPositions[col][idx].y }}
              />
            ))
          )}

          {/* Right match cards */}
          {rightRounds.map((round, col) =>
            round.map((match, idx) => (
              <BracketCard
                key={match.id}
                match={match}
                teams={teams}
                flip={true}
                style={{ left: rightPositions[col][idx].x, top: rightPositions[col][idx].y }}
              />
            ))
          )}

          {/* Final */}
          {final.length > 0 && (
            <BracketCard
              match={final[0]}
              teams={teams}
              style={{ left: centerX, top: finalY }}
            />
          )}

          {/* 3rd place */}
          {thirdPlace.length > 0 && (
            <>
              <div
                className="absolute text-[11px] font-semibold text-gray-400 uppercase tracking-wide"
                style={{ left: centerX, top: totalHeight + HEADER_H + 30, width: CARD_W, textAlign: 'center' }}
              >
                3.º Lugar
              </div>
              <BracketCard
                match={thirdPlace[0]}
                teams={teams}
                style={{ left: centerX, top: totalHeight + HEADER_H + 48 }}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
