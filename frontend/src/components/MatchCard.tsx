import { useState, useEffect } from 'react';
import type { Match, Team, Prediction } from '../api/types';
import { createPrediction, updatePrediction, listMatchPredictions } from '../api/predictions';

interface Props {
  match: Match;
  teams: Record<string, Team>;
  prediction?: Prediction;
  leagueId: string;
  userNames?: Record<string, string>;
  onPredictionSaved: () => void;
}

export default function MatchCard({ match, teams, prediction, leagueId, userNames = {}, onPredictionSaved }: Props) {
  const [homeScore, setHomeScore] = useState(prediction?.home_score?.toString() ?? '');
  const [awayScore, setAwayScore] = useState(prediction?.away_score?.toString() ?? '');

  useEffect(() => {
    setHomeScore(prediction?.home_score?.toString() ?? '');
    setAwayScore(prediction?.away_score?.toString() ?? '');
  }, [prediction?.home_score, prediction?.away_score]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [showOthers, setShowOthers] = useState(false);
  const [otherPreds, setOtherPreds] = useState<Prediction[] | null>(null);
  const [loadingOthers, setLoadingOthers] = useState(false);

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
    SF: 'Meias',
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

  const handleShowOthers = async () => {
    if (showOthers) {
      setShowOthers(false);
      return;
    }
    if (otherPreds === null) {
      setLoadingOthers(true);
      try {
        const preds = await listMatchPredictions(match.id, leagueId);
        setOtherPreds(preds);
      } catch {
        setOtherPreds([]);
      } finally {
        setLoadingOthers(false);
      }
    }
    setShowOthers(true);
  };

  const getPredictionStyle = () => {
    if (!prediction || !isFinished || match.home_score === null || match.away_score === null) return '';

    if (prediction.home_score === match.home_score && prediction.away_score === match.away_score) {
      return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    }

    const predOutcome = Math.sign(prediction.home_score - prediction.away_score);
    const realOutcome = Math.sign(match.home_score - match.away_score);
    if (predOutcome === realOutcome) {
      return 'text-yellow-700 bg-yellow-50 border-yellow-200';
    }

    return 'text-red-500 bg-red-50 border-red-200';
  };

  const getPredictionLabel = () => {
    if (!prediction || !isFinished || match.home_score === null || match.away_score === null) return '';

    if (prediction.home_score === match.home_score && prediction.away_score === match.away_score) {
      return 'Exato!';
    }

    const predOutcome = Math.sign(prediction.home_score - prediction.away_score);
    const realOutcome = Math.sign(match.home_score - match.away_score);
    if (predOutcome === realOutcome) {
      return 'Resultado certo';
    }

    return 'Errado';
  };

  const getOtherPredStyle = (pred: Prediction) => {
    if (!isFinished || match.home_score === null || match.away_score === null) return 'text-gray-600';

    if (pred.home_score === match.home_score && pred.away_score === match.away_score) {
      return 'text-emerald-600 font-bold';
    }

    const predOutcome = Math.sign(pred.home_score - pred.away_score);
    const realOutcome = Math.sign(match.home_score - match.away_score);
    if (predOutcome === realOutcome) {
      return 'text-yellow-700';
    }

    return 'text-red-400';
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-xl p-3 shadow-sm ${isFinished ? 'opacity-80' : 'active:shadow-md transition-shadow'}`}>
      {/* Header row */}
      <div className="flex justify-between items-center mb-2">
        <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded-full">
          {stageLabel[match.stage] ?? match.stage}
        </span>
        <span className="text-[10px] text-gray-400">
          {new Date(match.match_date).toLocaleDateString('pt-PT', {
            day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
          })}
        </span>
      </div>

      {/* Teams + Score row */}
      <div className="flex items-center justify-between gap-2">
        {/* Home */}
        <div className="flex-1 text-right min-w-0">
          <div className="flex items-center justify-end gap-1.5">
            <span className="font-semibold text-xs text-gray-800 truncate">{homeName}</span>
            {homeFlag && <img src={homeFlag} alt="" className="w-5 h-3.5 object-cover rounded-sm shadow-sm shrink-0" />}
          </div>
        </div>

        {/* Score / Input */}
        <div className="flex items-center gap-1 min-w-[100px] justify-center shrink-0">
          {isFinished ? (
            <div className="bg-gray-800 text-white px-2.5 py-1 rounded-lg">
              <span className="text-base font-bold">{match.home_score} - {match.away_score}</span>
            </div>
          ) : isPast ? (
            prediction ? (
              <span className="text-xs text-gray-500 bg-gray-100 px-2.5 py-1 rounded-lg">
                {prediction.home_score} - {prediction.away_score}
              </span>
            ) : (
              <span className="text-[10px] text-gray-400 bg-gray-50 px-2.5 py-1 rounded-lg">Fechado</span>
            )
          ) : (
            <>
              <input
                type="number"
                inputMode="numeric"
                pattern="[0-9]*"
                min="0"
                max="20"
                value={homeScore}
                onChange={(e) => setHomeScore(e.target.value)}
                className="w-10 h-9 text-center border border-gray-300 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
              <span className="text-gray-300 font-bold text-sm">-</span>
              <input
                type="number"
                inputMode="numeric"
                pattern="[0-9]*"
                min="0"
                max="20"
                value={awayScore}
                onChange={(e) => setAwayScore(e.target.value)}
                className="w-10 h-9 text-center border border-gray-300 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </>
          )}
        </div>

        {/* Away */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            {awayFlag && <img src={awayFlag} alt="" className="w-5 h-3.5 object-cover rounded-sm shadow-sm shrink-0" />}
            <span className="font-semibold text-xs text-gray-800 truncate">{awayName}</span>
          </div>
        </div>
      </div>

      {/* My prediction vs result */}
      {isFinished && prediction && (
        <div className={`mt-2 text-center text-[11px] font-medium px-2 py-1 rounded-lg border ${getPredictionStyle()}`}>
          Aposta: {prediction.home_score} - {prediction.away_score} · {getPredictionLabel()}
        </div>
      )}

      {/* Submit button */}
      {!isPast && !isFinished && (
        <div className="mt-2 flex justify-center">
          <button
            onClick={handleSubmit}
            disabled={saving || homeScore === '' || awayScore === ''}
            className="text-xs bg-emerald-600 text-white px-6 py-2 rounded-lg active:bg-emerald-700 disabled:opacity-40 font-medium transition-colors"
          >
            {saving ? 'A guardar...' : prediction ? 'Atualizar' : 'Submeter'}
          </button>
        </div>
      )}

      {error && <p className="text-red-500 text-xs text-center mt-1.5">{error}</p>}

      {prediction && !isPast && !isFinished && (
        <p className="text-emerald-600 text-[11px] text-center mt-1.5 font-medium">
          Aposta: {prediction.home_score} - {prediction.away_score}
        </p>
      )}

      {/* Show others' predictions */}
      {isPast && (
        <div className="mt-2">
          <button
            onClick={handleShowOthers}
            disabled={loadingOthers}
            className="text-[11px] text-gray-500 active:text-emerald-600 font-medium transition-colors w-full text-center py-1"
          >
            {loadingOthers ? 'A carregar...' : showOthers ? 'Esconder apostas' : 'Ver apostas da liga'}
          </button>

          {showOthers && otherPreds && (
            <div className="mt-1.5 space-y-0.5">
              {otherPreds.length === 0 ? (
                <p className="text-[11px] text-gray-400 text-center">Ninguém apostou neste jogo.</p>
              ) : (
                otherPreds.map((pred) => (
                  <div key={pred.id} className="flex justify-between items-center text-[11px] px-2.5 py-1.5 bg-gray-50 rounded-lg">
                    <span className="text-gray-700">{userNames[pred.user_id] ?? 'Utilizador'}</span>
                    <span className={getOtherPredStyle(pred)}>
                      {pred.home_score} - {pred.away_score}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
