import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { League } from '../api/types';
import { listLeagues } from '../api/leagues';
import { useAuth } from './AuthContext';

interface LeagueContextType {
  leagues: League[];
  activeLeague: League | null;
  setActiveLeagueId: (id: string) => void;
  refreshLeagues: () => Promise<void>;
}

const LeagueContext = createContext<LeagueContextType>(null!);

export function LeagueProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [activeLeagueId, setActiveLeagueIdState] = useState<string | null>(
    localStorage.getItem('activeLeagueId')
  );

  const setActiveLeagueId = (id: string) => {
    setActiveLeagueIdState(id);
    localStorage.setItem('activeLeagueId', id);
  };

  const refreshLeagues = async () => {
    try {
      const data = await listLeagues();
      setLeagues(data);

      // Auto-select first league if none selected or current is invalid
      if (data.length > 0) {
        const currentValid = data.some((l) => l.id === activeLeagueId);
        if (!currentValid) {
          setActiveLeagueId(data[0].id);
        }
      }
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    if (user) refreshLeagues();
  }, [user]);

  const activeLeague = leagues.find((l) => l.id === activeLeagueId) ?? leagues[0] ?? null;

  return (
    <LeagueContext.Provider value={{ leagues, activeLeague, setActiveLeagueId, refreshLeagues }}>
      {children}
    </LeagueContext.Provider>
  );
}

export function useLeague() {
  return useContext(LeagueContext);
}
