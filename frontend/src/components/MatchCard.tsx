import { useState, useEffect } from 'react';
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

  useEffect(() => {
    setHomeScore(prediction?.home_score?.toString() ?? '');
    setAwayScore(prediction?.away_score?.toString() ?? '');
  }, [prediction?.home_score, prediction?.away_score]);
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
    R32: '16 Avos',
    R16: 'Oitavos',
    QF: 'Quartos',
    SF: 'Meias-finais',
    '3rd': '3.º Lugar',
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
    <div className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${isFinished ? 'opacity-60' : 'hover:shadow-md transition-shadow'}`}>
      <div className="flex justify-between items-center mb-3">
        <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
          {stageLabel[match.stage] ?? match.stage}
        </span>
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
            <span className="font-semibold text-sm text-gray-800">{homeName}</span>
            {homeFlag && <img src={homeFlag} alt="" className="w-6 h-4 object-cover rounded-sm shadow-sm" />}
          </div>
        </div>

        {/* Score / Input */}
        <div className="flex items-center gap-1.5 min-w-[110px] justify-center">
          {isFinished ? (
            <div className="bg-gray-800 text-white px-3 py-1 rounded-lg">
              <span className="text-lg font-bold">{match.home_score} - {match.away_score}</span>
            </div>
          ) : isPast ? (
            prediction ? (
              <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-lg">
                {prediction.home_score} - {prediction.away_score}
              </span>
            ) : (
              <span className="text-xs text-gray-400 bg-gray-50 px-3 py-1 rounded-lg">Fechado</span>
            )
          ) : (
            <>
              <input
                type="number"
                min="0"
                max="20"
                value={homeScore}
                onChange={(e) => setHomeScore(e.target.value)}
                className="w-11 text-center border border-gray-300 rounded-lg py-1.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
              <span className="text-gray-300 font-bold">-</span>
              <input
                type="number"
                min="0"
                max="20"
                value={awayScore}
                onChange={(e) => setAwayScore(e.target.value)}
                className="w-11 text-center border border-gray-300 rounded-lg py-1.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </>
          )}
        </div>

        {/* Away */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            {awayFlag && <img src={awayFlag} alt="" className="w-6 h-4 object-cover rounded-sm shadow-sm" />}
            <span className="font-semibold text-sm text-gray-800">{awayName}</span>
          </div>
        </div>
      </div>

      {/* Submit button */}
      {!isPast && !isFinished && (
        <div className="mt-3 flex justify-center">
          <button
            onClick={handleSubmit}
            disabled={saving || homeScore === '' || awayScore === ''}
            className="text-xs bg-emerald-600 text-white px-5 py-1.5 rounded-lg hover:bg-emerald-700 disabled:opacity-40 font-medium transition-colors"
          >
            {saving ? 'A guardar...' : prediction ? 'Atualizar' : 'Submeter'}
          </button>
        </div>
      )}

      {error && <p className="text-red-500 text-xs text-center mt-2">{error}</p>}

      {prediction && !isPast && !isFinished && (
        <p className="text-emerald-600 text-xs text-center mt-2 font-medium">
          Aposta: {prediction.home_score} - {prediction.away_score}
        </p>
      )}
    </div>
  );
}
