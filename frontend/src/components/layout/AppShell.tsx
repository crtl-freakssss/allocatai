import React from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
    LayoutDashboard,
    FileText,
    FolderKanban,
    Dna,
    Map,
    SlidersHorizontal,
    Wallet,
    RefreshCw,
    ShieldCheck,
    Lightbulb,
    History,
    Settings,
} from 'lucide-react'

const navigation = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Proposals', path: '/proposals', icon: FileText },
    { label: 'Projects', path: '/projects', icon: FolderKanban },
    { label: 'Impact DNA', path: '/projects/PRJ-0001/impact-dna', icon: Dna },
    { label: 'Saturation', path: '/saturation', icon: Map },
    { label: 'Budget Optimizer', path: '/optimization', icon: SlidersHorizontal },
    { label: 'Allocations', path: '/allocations', icon: Wallet },
    { label: 'Reallocation', path: '/reallocation', icon: RefreshCw },
    { label: 'Due Diligence', path: '/due-diligence', icon: ShieldCheck },
    { label: 'Explainability', path: '/explainability', icon: Lightbulb },
    { label: 'Audit', path: '/audit', icon: History },
    { label: 'Settings', path: '/settings', icon: Settings },
]

export const AppShell: React.FC = () => {
    return (
        <div className="min-h-screen bg-background text-on-surface">
            <div className="flex min-h-screen">

                {/* Sidebar */}
                <aside className="w-60 shrink-0 border-r border-outline-variant/50 bg-surface-container-low">
                    <div className="sticky top-0">
                        {/* Brand */}
                        <div className="border-b border-outline-variant/50 px-5 py-5">
                            <h1 className="font-headline-md text-headline-md font-bold tracking-tight text-on-surface">
                                Allocate<span className="text-secondary">AI</span>
                            </h1>
                            <p className="mt-0.5 font-label-caps text-label-caps uppercase text-on-surface-variant">
                                CSR Decision Platform
                            </p>
                        </div>

                        {/* Nav */}
                        <nav className="p-3 space-y-0.5">
                            {navigation.map((item) => (
                                <NavLink
                                    key={item.path}
                                    to={item.path}
                                    className={({ isActive }) =>
                                        `flex items-center gap-3 rounded-lg px-3 py-2 font-body-md text-[13px] font-medium transition-colors ${
                                            isActive
                                                ? 'bg-secondary/10 text-secondary'
                                                : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                                        }`
                                    }
                                >
                                    <item.icon size={16} className="shrink-0" />
                                    <span>{item.label}</span>
                                </NavLink>
                            ))}
                        </nav>
                    </div>
                </aside>

                {/* Main content area */}
                <div className="flex flex-1 flex-col min-w-0">
                    {/* Top header bar */}
                    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-outline-variant/50 bg-surface-container-lowest px-8 py-3.5 shadow-xs">
                        <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                            CSR Decision Platform
                        </p>
                        <div className="flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                            <span className="font-label-caps text-[11px] uppercase text-emerald-700 font-semibold">FastAPI Engine Live</span>
                        </div>
                    </header>

                    {/* Page canvas */}
                    <main className="flex-1 bg-background p-8">
                        <Outlet />
                    </main>
                </div>

            </div>
        </div>
    )
}

export default AppShell
