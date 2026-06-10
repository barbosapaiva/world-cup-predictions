import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLeague } from '../context/LeagueContext';

export default function Layout() {
  const { user, logout } = useAuth();
  const { leagues, activeLeague, setActiveLeagueId } = useLeague();
  const location = useLocation();

  const leagueId = activeLeague?.id ?? '';

  const navItems = [
    { path: '/leagues', label: 'Ligas', href: '/leagues' },
    { path: '/matches', label: 'Jogos', href: `/matches?league=${leagueId}` },
    { path: '/ranking', label: 'Ranking', href: `/ranking?league=${leagueId}` },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-emerald-800 sticky top-0 z-10 shadow-lg">
        <div className="max-w-5xl mx-auto px-4 flex items-center justify-between h-14">
          <Link to="/leagues" className="font-extrabold text-lg text-white tracking-tight">
            WC 2026
          </Link>

          <div className="flex items-center gap-4">
            {/* League selector */}
            {leagues.length > 0 && (
              <select
                value={activeLeague?.id ?? ''}
                onChange={(e) => setActiveLeagueId(e.target.value)}
                className="bg-emerald-700 text-white text-xs rounded-lg px-2 py-1.5 border border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-400 cursor-pointer"
              >
                {leagues.map((l) => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            )}

            {/* Nav links */}
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.href}
                className={`text-sm font-medium transition-colors ${
                  location.pathname.startsWith(item.path)
                    ? 'text-white'
                    : 'text-emerald-300 hover:text-white'
                }`}
              >
                {item.label}
              </Link>
            ))}

            <div className="flex items-center gap-3 ml-2 pl-4 border-l border-emerald-700">
              <span className="text-xs text-emerald-300">{user?.name}</span>
              <button
                onClick={logout}
                className="text-xs text-emerald-400 hover:text-white transition-colors"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main>
        <Outlet />
      </main>
    </div>
  );
}
