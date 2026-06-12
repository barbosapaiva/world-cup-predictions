import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLeague } from '../context/LeagueContext';

export default function Layout() {
  const { user, logout } = useAuth();
  const { leagues, activeLeague, setActiveLeagueId } = useLeague();
  const location = useLocation();
  const navigate = useNavigate();

  const leagueId = activeLeague?.id ?? '';

  const handleLeagueChange = (id: string) => {
    setActiveLeagueId(id);
    navigate(`/leagues/${id}`);
  };

  const navItems = [
    { path: '/leagues', exact: true, label: 'Ligas', href: '/leagues' },
    { path: '/matches', exact: false, label: 'Jogos', href: `/matches?league=${leagueId}` },
    { path: '/ranking', exact: false, label: 'Ranking', href: `/ranking?league=${leagueId}` },
  ];

  const isLeagueDetail = /^\/leagues\/[^/]+$/.test(location.pathname);

  const getIsActive = (item: typeof navItems[0]): boolean => {
    if (item.path === '/leagues' && item.exact) {
      return location.pathname === '/leagues' || isLeagueDetail;
    }
    return location.pathname.startsWith(item.path);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* ── Top bar ── */}
      <nav className="bg-emerald-800 sticky top-0 z-30 safe-top shadow-lg">
        <div className="max-w-5xl mx-auto px-3 flex items-center justify-between h-12">
          {/* Logo */}
          <span
            onClick={() => navigate('/leagues')}
            className="font-extrabold text-base text-white tracking-tight cursor-pointer select-none shrink-0"
          >
            WC 2026
          </span>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const active = getIsActive(item);
              return (
                <button
                  key={item.path}
                  onClick={() => navigate(item.href)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    active
                      ? 'bg-emerald-700 text-white'
                      : 'text-emerald-300 active:text-white'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </div>

          {/* Right: league selector + user */}
          <div className="flex items-center gap-2 shrink-0">
            {leagues.length > 0 && (
              <select
                value={activeLeague?.id ?? ''}
                onChange={(e) => handleLeagueChange(e.target.value)}
                className="bg-emerald-700 text-white text-[11px] rounded-lg px-1.5 py-1 border border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-400 cursor-pointer max-w-[100px] truncate"
              >
                {leagues.map((l) => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            )}
            <span className="text-[11px] text-emerald-300 hidden sm:inline truncate max-w-[80px]">{user?.name}</span>
            <button
              onClick={logout}
              className="text-[11px] text-emerald-400 hover:text-white active:text-white transition-colors px-1"
              title="Sair"
            >
              Sair
            </button>
          </div>
        </div>
      </nav>

      {/* ── Main content ── */}
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
