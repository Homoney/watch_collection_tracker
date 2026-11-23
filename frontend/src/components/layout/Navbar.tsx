import { Link, useLocation } from 'react-router-dom'
import {
  BarChart3,
  Library,
  LayoutDashboard,
  LogOut,
  MoreHorizontal,
  Settings,
  Shield,
  Watch,
  type LucideIcon,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import ThemeToggle from './ThemeToggle'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

const mainItems: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/watches', label: 'Watches', icon: Watch },
  { to: '/collections', label: 'Collections', icon: Library },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
]

/** Top bar on every screen; the page links move to a bottom tab bar on phones. */
export default function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const isAdmin = user?.role === 'admin'

  // /watches/123 still marks Watches as the current section
  const isActive = (path: string) =>
    location.pathname === path || location.pathname.startsWith(`${path}/`)

  const desktopItems: NavItem[] = [
    ...mainItems,
    ...(isAdmin ? [{ to: '/admin', label: 'Admin', icon: Shield }] : []),
    { to: '/settings', label: 'Settings', icon: Settings },
  ]
  const moreActive = isActive('/settings') || isActive('/admin') || isActive('/compare')

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-10">
            <Link
              to="/dashboard"
              className="text-[13px] font-semibold uppercase tracking-[0.32em] text-foreground"
            >
              Watch <span className="text-gold">Tracker</span>
            </Link>
            <nav aria-label="Main" className="hidden items-center gap-7 md:flex">
              {desktopItems.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  aria-current={isActive(item.to) ? 'page' : undefined}
                  className={cn(
                    'text-[11px] uppercase tracking-[0.2em] transition-colors hover:text-foreground',
                    isActive(item.to) ? 'text-gold' : 'text-muted-foreground'
                  )}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          <div className="flex min-w-0 items-center gap-2">
            <span className="hidden truncate text-xs text-muted-foreground lg:inline">{user?.email}</span>
            <ThemeToggle />
            <button
              type="button"
              onClick={logout}
              className="hidden h-9 items-center gap-2 px-2 text-[11px] uppercase tracking-[0.2em] text-muted-foreground hover:text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:inline-flex"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Phone: bottom tab bar (the top-bar links are hidden below md) */}
      <nav
        aria-label="Main"
        className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
      >
        <ul className="grid grid-cols-5">
          {mainItems.map(({ to, label, icon: Icon }) => (
            <li key={to}>
              <Link
                to={to}
                aria-current={isActive(to) ? 'page' : undefined}
                className={cn(
                  'flex h-16 flex-col items-center justify-center gap-1 text-[10px] uppercase tracking-[0.06em]',
                  isActive(to) ? 'text-gold' : 'text-muted-foreground'
                )}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
                {label}
              </Link>
            </li>
          ))}
          <li>
            <DropdownMenu>
              <DropdownMenuTrigger
                className={cn(
                  'flex h-16 w-full flex-col items-center justify-center gap-1 text-[10px] uppercase tracking-[0.06em] focus-visible:outline-none',
                  moreActive ? 'text-gold' : 'text-muted-foreground'
                )}
              >
                <MoreHorizontal className="h-5 w-5" aria-hidden="true" />
                More
              </DropdownMenuTrigger>
              <DropdownMenuContent side="top" align="end" className="min-w-[12rem]">
                {user?.email && (
                  <>
                    <DropdownMenuLabel className="truncate text-xs font-normal text-muted-foreground">
                      {user.email}
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                  </>
                )}
                <DropdownMenuItem asChild>
                  <Link to="/settings">
                    <Settings className="mr-2 h-4 w-4" /> Settings
                  </Link>
                </DropdownMenuItem>
                {isAdmin && (
                  <DropdownMenuItem asChild>
                    <Link to="/admin">
                      <Shield className="mr-2 h-4 w-4" /> Admin
                    </Link>
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem onSelect={logout}>
                  <LogOut className="mr-2 h-4 w-4" /> Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </li>
        </ul>
      </nav>
    </>
  )
}
