import { useState, useEffect } from 'react';
import { submitGroupPrediction } from '../api/groupPredictions';
import type { Team, GroupPrediction } from '../api/types';

interface Props {
  groupLetter: string;
  teams: Team[];
  leagueId: string;
  existing: GroupPrediction | null;
  locked?: boolean;
  othersPredictions?: GroupPrediction[];
  userNames?: Record<string, string>;
  onSaved: () => void;
}

export default function GroupPredictionCard({
  groupLetter, teams, leagueId, existing, locked = false,
  othersPredictions = [], userNames = {}, onSaved,
}: Props) {
  const [positions, setPositions] = useState<(string | null)[]>([null, null, null, null]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (existing) {
      setPositions([
        existing.first_team_id,
        existing.second_team_id,
        existing.third_team_id,
        existing.fourth_team_id,
      ]);
    }
  }, [existing]);

  const handleSelect = (posIndex: number, teamId: string) => {
    setPositions((prev) => {
      const next = [...prev];
      const existingIndex = next.indexOf(teamId);
      if (existingIndex !== -1 && existingIndex !== posIndex) {
        next[existingIndex] = next[posIndex];
      }
      next[posIndex] = teamId;
      return next;
    });
    setSaved(false);
  };

  const allSelected = positions.every((p) => p !== null);

  const handleSubmit = async () => {
    if (!allSelected) return;
    setSaving(true);
    try {
      await submitGroupPrediction(leagueId, {
        group_letter: groupLetter,
        first_team_id: positions[0]!,
        second_team_id: positions[1]!,
        third_team_id: positions[2]!,
        fourth_team_id: positions[3]!,
      });
      setSaved(true);
      onSaved();
    } catch {
      alert('Erro ao guardar previsão');
    } finally {
      setSaving(false);
    }
  };

  const teamMap = teams.reduce<Record<string, Team>>((acc, t) => { acc[t.id] = t; return acc; }, {});
  const getTeamName = (id: string | null) => id ? teamMap[id] : undefined;

  const labels = ['1º', '2º', '3º', '4º'];

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-bold text-gray-800">Grupo {groupLetter}</h3>
        {existing && existing.points_awarded !== null && (
          <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
            {existing.points_awarded} pt{existing.points_awarded !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className="space-y-2">
        {labels.map((label, i) => {
          const selected = getTeamName(positions[i]);
          return (
            <div key={i} className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-400 w-6">{label}</span>
              <select
                value={positions[i] || ''}
                onChange={(e) => handleSelect(i, e.target.value)}
                disabled={locked}
                className={`flex-1 text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-500 ${locked ? 'bg-gray-50 text-gray-400 cursor-not-allowed' : 'bg-white'}`}
              >
                <option value="">Selecionar...</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.code} — {t.name}
                  </option>
                ))}
              </select>
              {selected?.flag_url && (
                <img src={selected.flag_url} alt="" className="w-5 h-4 object-cover rounded-sm" />
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-3 flex items-center justify-between">
        {existing?.updated_at ? (
          <span className="text-xs text-gray-400">
            Atualizado: {new Date(existing.updated_at).toLocaleDateString('pt-PT', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
          </span>
        ) : <span />}
        {locked ? (
          <span className="text-xs text-gray-400 font-medium">Previsões encerradas</span>
        ) : saved ? (
          <span className="text-xs text-emerald-600 font-medium">Guardado</span>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!allSelected || saving}
            className="text-xs font-medium px-3 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? 'A guardar...' : existing ? 'Atualizar' : 'Guardar'}
          </button>
        )}
      </div>

      {/* Others' predictions — collapsible */}
      {locked && othersPredictions.length > 0 && (
        <div className="mt-3 border-t border-gray-100 pt-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-between text-xs text-gray-500 hover:text-gray-700 py-1"
          >
            <span className="font-medium">Apostas dos outros ({othersPredictions.length})</span>
            <span className="text-[10px]">{expanded ? '▲' : '▼'}</span>
          </button>
          {expanded && (
            <div className="mt-2 space-y-3">
              {othersPredictions.map((pred) => (
                <div key={pred.id} className="bg-gray-50 rounded-lg px-3 py-2">
                  <p className="text-xs font-semibold text-gray-700 mb-1">
                    {userNames[pred.user_id] || 'Utilizador'}
                  </p>
                  <div className="flex gap-1.5 flex-wrap">
                    {[pred.first_team_id, pred.second_team_id, pred.third_team_id, pred.fourth_team_id].map((tid, i) => {
                      const team = teamMap[tid];
                      return (
                        <span key={i} className="inline-flex items-center gap-1 text-[11px] text-gray-600 bg-white rounded px-1.5 py-0.5 border border-gray-200">
                          <span className="text-gray-400 font-medium">{i + 1}º</span>
                          {team?.flag_url && <img src={team.flag_url} alt="" className="w-4 h-3 object-cover rounded-sm" />}
                          {team?.code || '?'}
                        </span>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
