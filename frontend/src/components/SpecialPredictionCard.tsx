import { useState, useEffect, useRef, useMemo } from 'react';
import { submitSpecialPrediction } from '../api/specialPredictions';
import type { Team, Player, SpecialPrediction, SpecialCategory } from '../api/types';

// Young player cutoff: born on or after 1 Jan 2005 (max 21 years old)
const YOUNG_PLAYER_CUTOFF = '2005-01-01';

// Special predictions deadline
const SPECIAL_DEADLINE = new Date('2026-06-18T17:00:00Z');

interface Props {
  category: SpecialCategory;
  label: string;
  description: string;
  type: 'team' | 'player';
  teams: Team[];
  players: Player[];
  leagueId: string;
  existing: SpecialPrediction | null;
  onSaved: () => void;
}

export default function SpecialPredictionCard({
  category, label, description, type, teams, players, leagueId, existing, onSaved,
}: Props) {
  const [selectedTeamId, setSelectedTeamId] = useState<string>('');
  const [selectedPlayerId, setSelectedPlayerId] = useState<string>('');
  const [search, setSearch] = useState<string>('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const locked = new Date() >= SPECIAL_DEADLINE;

  // Filter players based on category
  const eligiblePlayers = useMemo(() => {
    if (category === 'best_gk') {
      return players.filter((p) => p.position === 'GK');
    }
    if (category === 'young_player') {
      return players.filter((p) => p.birth_date && p.birth_date >= YOUNG_PLAYER_CUTOFF);
    }
    return players;
  }, [players, category]);

  // Initialize from existing prediction
  useEffect(() => {
    if (existing) {
      if (type === 'team' && existing.team_id) {
        setSelectedTeamId(existing.team_id);
      } else if (type === 'player' && existing.player_id) {
        setSelectedPlayerId(existing.player_id);
        const player = eligiblePlayers.find((p) => p.id === existing.player_id)
          ?? players.find((p) => p.id === existing.player_id);
        if (player) setSearch(player.name);
      }
    }
  }, [existing, players, eligiblePlayers]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // Build team lookup for showing team code next to player name
  const teamMap = teams.reduce<Record<string, Team>>((acc, t) => { acc[t.id] = t; return acc; }, {});

  const filteredPlayers = search.length >= 2
    ? eligiblePlayers.filter((p) => p.name.toLowerCase().includes(search.toLowerCase())).slice(0, 15)
    : [];

  const canSubmit = type === 'team' ? !!selectedTeamId : !!selectedPlayerId;

  const handleSelectPlayer = (player: Player) => {
    setSelectedPlayerId(player.id);
    setSearch(player.name);
    setShowDropdown(false);
    setSaved(false);
  };

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSaving(true);
    try {
      await submitSpecialPrediction({
        league_id: leagueId,
        category,
        team_id: type === 'team' ? selectedTeamId : undefined,
        player_id: type === 'player' ? selectedPlayerId : undefined,
      });
      setSaved(true);
      onSaved();
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Erro ao guardar';
      alert(detail);
    } finally {
      setSaving(false);
    }
  };

  const hasChanged = () => {
    if (!existing) return canSubmit;
    if (type === 'team') return existing.team_id !== selectedTeamId;
    return existing.player_id !== selectedPlayerId;
  };

  const placeholder = category === 'best_gk'
    ? 'Pesquisar guarda-redes...'
    : category === 'young_player'
      ? 'Pesquisar jogador sub-21...'
      : 'Escrever nome do jogador...';

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <div className="flex justify-between items-start mb-1">
        <h3 className="font-bold text-gray-800">{label}</h3>
        {existing && (
          <span className="text-xs text-gray-400">Submetido</span>
        )}
      </div>
      <p className="text-xs text-gray-400 mb-3">{description}</p>

      {locked ? (
        <div className="text-xs text-gray-400 bg-gray-50 rounded-lg px-3 py-2 text-center font-medium">
          {existing ? (
            <>Aposta: {type === 'team'
              ? teams.find((t) => t.id === existing.team_id)?.name ?? '—'
              : players.find((p) => p.id === existing.player_id)?.name ?? '—'
            }</>
          ) : 'Sem aposta'}
        </div>
      ) : type === 'team' ? (
        <select
          value={selectedTeamId}
          onChange={(e) => { setSelectedTeamId(e.target.value); setSaved(false); }}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2.5 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
        >
          <option value="">Selecionar equipa...</option>
          {teams.map((t) => (
            <option key={t.id} value={t.id}>{t.code} — {t.name}</option>
          ))}
        </select>
      ) : (
        <div ref={wrapperRef} className="relative">
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setSelectedPlayerId('');
              setSaved(false);
              setShowDropdown(true);
            }}
            onFocus={() => search.length >= 2 && setShowDropdown(true)}
            placeholder={placeholder}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2.5 bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          {showDropdown && filteredPlayers.length > 0 && (
            <ul className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
              {filteredPlayers.map((p) => (
                <li
                  key={p.id}
                  onClick={() => handleSelectPlayer(p)}
                  className="px-3 py-2.5 text-sm active:bg-emerald-50 cursor-pointer flex justify-between"
                >
                  <span>{p.name}</span>
                  <span className="text-gray-400 text-xs">{teamMap[p.team_id]?.code || ''}</span>
                </li>
              ))}
            </ul>
          )}
          {search.length >= 2 && filteredPlayers.length === 0 && showDropdown && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-sm text-gray-400">
              Nenhum jogador encontrado
            </div>
          )}
        </div>
      )}

      <div className="mt-3 flex items-center justify-between">
        {existing?.submitted_at ? (
          <span className="text-[10px] text-gray-400">
            {new Date(existing.submitted_at).toLocaleDateString('pt-PT', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
          </span>
        ) : <span />}
        {locked ? (
          <span className="text-xs text-gray-400 font-medium">Encerrado</span>
        ) : saved ? (
          <span className="text-xs text-emerald-600 font-medium">Guardado</span>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!hasChanged() || saving}
            className="text-xs font-medium px-3 py-1.5 rounded-lg bg-emerald-600 text-white active:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? 'A guardar...' : existing ? 'Atualizar' : 'Guardar'}
          </button>
        )}
      </div>
    </div>
  );
}
