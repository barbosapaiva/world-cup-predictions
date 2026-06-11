import { useRef, useState, useEffect } from 'react';
import type { Match, Team } from '../api/types';

interface Props {
  matches: Match[];
  teams: Record<string, Team>;
}

// Layout
const CARD_W = 160;
const CARD_H = 48;
const V_GAP = 8; // vertical gap between cards in same round
const COL_GAP = 36; // horizontal gap between rounds
const PAD = 12;

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

// Compute Y positions for a column of N cards, centered on totalHeight
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
  flip,
}: {
  name: string;
  flagUrl: string | null;
  score: number | null;
  isWinner: boolean;
  isFinished: boolean;
  isTop: boolean;
  flip?: boolean;
}) {
  const displayName = name.length > 12 ? name.slice(0, 10) + '…' : name;

  return (
    <div
      className={`flex items-center gap-1.5 px-2 py-1.5 ${
        isWinner ? 'bg-emerald-50' : 'bg-white'
      } ${isTop ? 'rounded-t-lg' : 'rounded-b-lg border-t border-gray-100'}`}
      style={{ width: CARD_W, height: CARD_H / 2 }}
    >
      {flip ? (
        <>
          <span className={`font-mono text-xs w-5 text-center ${isWinner ? 'font-bold text-emerald-700' : 'text-gray-400'}`}>
            {isFinished ? score : '-'}
          </span>
          <div className="flex-1 flex items-center justify-end gap-1.5 min-w-0">
            <span className={`text-xs truncate ${isWinner ? 'font-bold text-gray-800' : 'text-gray-600'}`}>
              {displayName}
            </span>
            {flagUrl && <img src={flagUrl} alt="" className="w-5 h-3.5 object-cover rounded-sm flex-shrink-0" />}
          </div>
        </>
      ) : (
        <>
          <div className="flex-1 flex items-center gap-1.5 min-w-0">
            {flagUrl && <img src={flagUrl} alt="" className="w-5 h-3.5 object-cover rounded-sm flex-shrink-0" />}
            <span className={`text-xs truncate ${isWinner ? 'font-bold text-gray-800' : 'text-gray-600'}`}>
              {displayName}
            </span>
          </div>
          <span className={`font-mono text-xs w-5 text-center ${isWinner ? 'font-bold text-emerald-700' : 'text-gray-400'}`}>
            {isFinished ? score : '-'}
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
      className="absolute border border-gray-200 rounded-lg shadow-sm overflow-hidden"
      style={{ ...style, width: CARD_W, height: CARD_H }}
    >
      <TeamRow
        name={getTeamName(match, teams, 'home')}
        flagUrl={getTeamFlag(match, teams, 'home')}
        score={match.home_score}
        isWinner={homeWon}
        isFinished={isFinished}
        isTop={true}
        flip={flip}
      />
      <TeamRow
        name={getTeamName(match, teams, 'away')}
        flagUrl={getTeamFlag(match, teams, 'away')}
        score={match.away_score}
        isWinner={awayWon}
        isFinished={isFinished}
        isTop={false}
        flip={flip}
      />
    </div>
  );
}

// Draw connector lines on SVG overlay
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

        // From source 1
        paths.push(`M ${exitX} ${s1Mid} H ${midX}`);
        paths.push(`M ${midX} ${s1Mid} V ${tMid}`);
        paths.push(`M ${midX} ${tMid} H ${enterX}`);

        // From source 2
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
        <path key={i} d={d} fill="none" stroke="#9ca3af" strokeWidth={2} />
      ))}
    </>
  );
}

export default function BracketView({ matches, teams }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  // Organize matches by stage
  const getStageMatches = (stages: string[]) =>
    matches
      .filter((m) => stages.includes(m.stage))
      .sort((a, b) => a.match_number - b.match_number);

  const r16 = getStageMatches(['R16', 'R32']);
  const qf = getStageMatches(['QF']);
  const sf = getStageMatches(['SF']);
  const final = getStageMatches(['F']);
  const thirdPlace = getStageMatches(['3rd']);

  // Split into left half and right half
  const leftR16 = r16.slice(0, Math.ceil(r16.length / 2));
  const rightR16 = r16.slice(Math.ceil(r16.length / 2));
  const leftQF = qf.slice(0, Math.ceil(qf.length / 2));
  const rightQF = qf.slice(Math.ceil(qf.length / 2));
  const leftSF = sf.slice(0, Math.ceil(sf.length / 2));
  const rightSF = sf.slice(Math.ceil(sf.length / 2));

  // Left side rounds (left to right: R16 → QF → SF)
  const leftRounds = [leftR16, leftQF, leftSF].filter((r) => r.length > 0);
  // Right side rounds (right to left: R16 → QF → SF, but displayed right to left)
  const rightRounds = [rightR16, rightQF, rightSF].filter((r) => r.length > 0);

  // Calculate total height from the largest column
  const maxCards = Math.max(leftR16.length, rightR16.length, 1);
  const totalHeight = maxCards * CARD_H + (maxCards - 1) * V_GAP;

  // Number of left columns + final column + right columns
  const leftCols = leftRounds.length;
  const centerWidth = CARD_W + COL_GAP * 2; // space for final
  const sideWidth = leftCols * (CARD_W + COL_GAP);
  const totalWidth = sideWidth * 2 + centerWidth + PAD * 2;

  // Compute positions for left side
  const leftPositions: { x: number; y: number }[][] = [];
  for (let col = 0; col < leftRounds.length; col++) {
    const x = PAD + col * (CARD_W + COL_GAP);
    const ys = distributeY(leftRounds[col].length, totalHeight);
    leftPositions.push(ys.map((y) => ({ x, y: y + 60 })));
  }

  // Compute positions for right side (mirrored)
  const rightPositions: { x: number; y: number }[][] = [];
  for (let col = 0; col < rightRounds.length; col++) {
    const x = totalWidth - PAD - CARD_W - col * (CARD_W + COL_GAP);
    const ys = distributeY(rightRounds[col].length, totalHeight);
    rightPositions.push(ys.map((y) => ({ x, y: y + 60 })));
  }

  // Final position (center)
  const centerX = totalWidth / 2 - CARD_W / 2;
  const finalY = totalHeight / 2 - CARD_H / 2 + 60;

  // Connect left SF to final
  const leftToFinalPaths: string[] = [];
  if (leftPositions.length > 0) {
    const lastLeft = leftPositions[leftPositions.length - 1];
    for (const pos of lastLeft) {
      const exitX = pos.x + CARD_W;
      const exitY = pos.y + CARD_H / 2;
      const enterX = centerX;
      const enterY = finalY + CARD_H / 2;
      const midX = exitX + (enterX - exitX) / 2;
      leftToFinalPaths.push(`M ${exitX} ${exitY} H ${midX}`);
      leftToFinalPaths.push(`M ${midX} ${exitY} V ${enterY}`);
      leftToFinalPaths.push(`M ${midX} ${enterY} H ${enterX}`);
    }
  }

  // Connect right SF to final
  const rightToFinalPaths: string[] = [];
  if (rightPositions.length > 0) {
    const lastRight = rightPositions[rightPositions.length - 1];
    for (const pos of lastRight) {
      const exitX = pos.x;
      const exitY = pos.y + CARD_H / 2;
      const enterX = centerX + CARD_W;
      const enterY = finalY + CARD_H / 2;
      const midX = exitX - (exitX - enterX) / 2;
      rightToFinalPaths.push(`M ${exitX} ${exitY} H ${midX}`);
      rightToFinalPaths.push(`M ${midX} ${exitY} V ${enterY}`);
      rightToFinalPaths.push(`M ${midX} ${enterY} H ${enterX}`);
    }
  }

  const svgHeight = totalHeight + 120 + (thirdPlace.length > 0 ? CARD_H + 50 : 0);

  // Stage labels
  const stageLabels = ['16 Avos', 'Oitavos', 'Meias'];

  // Auto-scale to fit viewport
  useEffect(() => {
    const update = () => {
      if (!containerRef.current) return;
      const parent = containerRef.current.parentElement;
      if (!parent) return;
      const availW = parent.clientWidth;
      const availH = window.innerHeight - containerRef.current.getBoundingClientRect().top - 16;
      const isMobile = availW < 640;
      if (isMobile) {
        // On mobile: fit height, allow horizontal scroll
        setScale(Math.min(availH / svgHeight, 0.45));
      } else {
        const scaleW = availW / totalWidth;
        const scaleH = availH / svgHeight;
        setScale(Math.min(scaleW, scaleH, 1));
      }
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, [totalWidth, svgHeight]);

  if (r16.length === 0 && qf.length === 0 && sf.length === 0 && final.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-400 text-lg">Ainda não há jogos eliminatórios.</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="overflow-x-auto sm:overflow-hidden sm:flex sm:justify-center" style={{ height: svgHeight * scale }}>
      <div className="relative origin-top-left sm:origin-top" style={{ width: totalWidth * scale, height: svgHeight * scale }}>
        <div className="absolute top-0 left-0" style={{ width: totalWidth, height: svgHeight, transform: `scale(${scale})`, transformOrigin: 'top left' }}>
        {/* SVG for lines */}
        <svg
          className="absolute inset-0 pointer-events-none"
          width={totalWidth}
          height={svgHeight}
        >
          {/* Left side connectors */}
          <ConnectorLines positions={leftPositions} side="left" />

          {/* Right side connectors */}
          <ConnectorLines positions={rightPositions} side="right" />

          {/* Left SF → Final */}
          {leftToFinalPaths.map((d, i) => (
            <path key={`lf-${i}`} d={d} fill="none" stroke="#9ca3af" strokeWidth={2} />
          ))}

          {/* Right SF → Final */}
          {rightToFinalPaths.map((d, i) => (
            <path key={`rf-${i}`} d={d} fill="none" stroke="#9ca3af" strokeWidth={2} />
          ))}
        </svg>

        {/* Stage labels - left side */}
        {leftRounds.map((_, col) => (
          <div
            key={`ll-${col}`}
            className="absolute text-xs font-semibold text-emerald-700"
            style={{
              left: PAD + col * (CARD_W + COL_GAP),
              top: 20,
              width: CARD_W,
              textAlign: 'center',
            }}
          >
            {stageLabels[col] ?? ''}
          </div>
        ))}

        {/* Final label */}
        {final.length > 0 && (
          <div
            className="absolute text-sm font-bold text-emerald-800"
            style={{
              left: centerX,
              top: 16,
              width: CARD_W,
              textAlign: 'center',
            }}
          >
            Final
          </div>
        )}

        {/* Stage labels - right side */}
        {rightRounds.map((_, col) => (
          <div
            key={`rl-${col}`}
            className="absolute text-xs font-semibold text-emerald-700"
            style={{
              left: totalWidth - PAD - CARD_W - col * (CARD_W + COL_GAP),
              top: 20,
              width: CARD_W,
              textAlign: 'center',
            }}
          >
            {stageLabels[col] ?? ''}
          </div>
        ))}

        {/* Left side match cards */}
        {leftRounds.map((round, col) =>
          round.map((match, idx) => (
            <BracketCard
              key={match.id}
              match={match}
              teams={teams}
              style={{
                left: leftPositions[col][idx].x,
                top: leftPositions[col][idx].y,
              }}
            />
          ))
        )}

        {/* Right side match cards (flipped: score on left, flag+name on right) */}
        {rightRounds.map((round, col) =>
          round.map((match, idx) => (
            <BracketCard
              key={match.id}
              match={match}
              teams={teams}
              flip={true}
              style={{
                left: rightPositions[col][idx].x,
                top: rightPositions[col][idx].y,
              }}
            />
          ))
        )}

        {/* Final card */}
        {final.length > 0 && (
          <BracketCard
            match={final[0]}
            teams={teams}
            style={{
              left: centerX,
              top: finalY,
            }}
          />
        )}

        {/* 3rd place */}
        {thirdPlace.length > 0 && (
          <>
            <div
              className="absolute text-xs font-semibold text-gray-500"
              style={{
                left: centerX,
                top: totalHeight + 80,
                width: CARD_W,
                textAlign: 'center',
              }}
            >
              3.º Lugar
            </div>
            <BracketCard
              match={thirdPlace[0]}
              teams={teams}
              style={{
                left: centerX,
                top: totalHeight + 100,
              }}
            />
          </>
        )}
        </div>
      </div>
    </div>
  );
}
