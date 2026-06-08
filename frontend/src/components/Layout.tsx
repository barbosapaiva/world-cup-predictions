import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { path: '/leagues', label: 'Ligas' },
  { path: '/matches', label: 'Jogos' },
  { path: '/ranking', label: 'Ranking' },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 flex items-center justify-between h-14">
          <Link to="/leagues" className="font-bold text-lg">WC 2026</Link>

          <div className="flex items-center gap-4">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`text-sm ${
                  location.pathname.startsWith(item.path)
                    ? 'text-blue-600 font-medium'
                    : 'text-gray-500 hover:text-gray-800'
                }`}
              >
                {item.label}
              </Link>
            ))}
            <span className="text-xs text-gray-400">{user?.name}</span>
            <button
              onClick={logout}
              className="text-xs text-red-500 hover:text-red-700"
            >
              Sair
            </button>
          </div>
        </div>
      </nav>

      <main>
        <Outlet />
      </main>
    </div>
  );
}
