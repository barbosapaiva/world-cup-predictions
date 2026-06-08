import { useState } from 'react';
import type { Match, Team, Prediction } from '../api/types';
import { createPrediction, updatePrediction } from '../api/predictions';

interface Props {
  match: Match;
  teams: Record<string, Team>;
  prediction?: Prediction;
  leagueId: string;
  onPredictionSaved: () => void;
}

export default function MatchCard({ match, teams, prediction, leagueId, onPredictionSaved }: Props) {
  const [homeScore, setHomeScore] = useState(prediction?.home_score?.toString() ?? '');
  const [awayScore, setAwayScore] = useState(prediction?.away_score?.toString() ?? '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const homeTeam = match.home_team_id ? teams[match.home_team_id] : null;
  const awayTeam = match.away_team_id ? teams[match.away_team_id] : null;
  const homeName = homeTeam?.name ?? match.home_placeholder ?? 'TBD';
  const awayName = awayTeam?.name ?? match.away_placeholder ?? 'TBD';
  const homeFlag = homeTeam?.flag_url;
  const awayFlag = awayTeam?.flag_url;

  const isPast = new Date(match.submission_deadline) < new Date();
  const isFinished = match.status === 'finished';

  const stageLabel: Record<string, string> = {
    group: `Grupo ${match.group_letter ?? ''}`,
    R32: 'Oitavos',
    R16: 'Oitavos',
    QF: 'Quartos',
    SF: 'Meias',
    '3rd': '3.o Lugar',
    F: 'Final',
  };

  const handleSubmit = async () => {
    if (homeScore === '' || awayScore === '') return;
    setError('');
    setSaving(true);
    try {
      if (prediction) {
        await updatePrediction(prediction.id, {
          home_score: parseInt(homeScore),
          away_score: parseInt(awayScore),
        });
      } else {
        await createPrediction({
          league_id: leagueId,
          match_id: match.id,
          home_score: parseInt(homeScore),
          away_score: parseInt(awayScore),
        });
      }
      onPredictionSaved();
    } catch {
      setError('Erro ao guardar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={`bg-white border rounded-lg p-4 ${isFinished ? 'opacity-70' : ''}`}>
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-gray-400">{stageLabel[match.stage] ?? match.stage}</span>
        <span className="text-xs text-gray-400">
          {new Date(match.match_date).toLocaleDateString('pt-PT', {
            day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
          })}
        </span>
      </div>

      <div className="flex items-center justify-between gap-4">
        {/* Home */}
        <div className="flex-1 text-right">
          <div className="flex items-center justify-end gap-2">
            <span className="font-medium text-sm">{homeName}</span>
            {homeFlag && <img src={homeFlag} alt="" className="w-6 h-4 object-cover" />}
          </div>
        </div>

        {/* Score / Input */}
        <div className="flex items-center gap-1 min-w-[100px] justify-center">
          {isFinished ? (
            <span className="text-lg font-bold">
              {match.home_score} - {match.away_score}
            </span>
          ) : isPast ? (
            prediction ? (
              <span className="text-sm text-gray-500">{prediction.home_score} - {prediction.away_score}</span>
            ) : (
              <span className="text-xs text-gray-400">Fechado</span>
            )
          ) : (
            <>
              <input
                type="number"
                min="0"
                max="20"
                value={homeScore}
                onChange={(e) => setHomeScore(e.target.value)}
                className="w-10 text-center border rounded py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <span className="text-gray-400">-</span>
              <input
                type="number"
                min="0"
                max="20"
                value={awayScore}
                onChange={(e) => setAwayScore(e.target.value)}
                className="w-10 text-center border rounded py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </>
          )}
        </div>

        {/* Away */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            {awayFlag && <img src={awayFlag} alt="" className="w-6 h-4 object-cover" />}
            <span className="font-medium text-sm">{awayName}</span>
          </div>
        </div>
      </div>

      {/* Submit button */}
      {!isPast && !isFinished && (
        <div className="mt-3 flex justify-center">
          <button
            onClick={handleSubmit}
            disabled={saving || homeScore === '' || awayScore === ''}
            className="text-xs bg-blue-600 text-white px-4 py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'A guardar...' : prediction ? 'Atualizar' : 'Submeter'}
          </button>
        </div>
      )}

      {error && <p className="text-red-500 text-xs text-center mt-1">{error}</p>}

      {prediction && !isPast && (
        <p className="text-green-600 text-xs text-center mt-1">
          Previsao: {prediction.home_score} - {prediction.away_score}
        </p>
      )}
    </div>
  );
}
