"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import {
  Activity, LayoutDashboard, FileText, MessageSquare,
  TrendingUp, Settings, LogOut, Bell
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/reports",   label: "Reports",   icon: FileText },
  { href: "/chat",      label: "AI Chat",   icon: MessageSquare },
  { href: "/trends",    label: "Trends",    icon: TrendingUp },
  { href: "/settings",  label: "Settings",  icon: Settings },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  return (
    <div className="flex h-screen bg-surface overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-surface-border bg-surface-card flex flex-col">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-surface-border">
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-xl bg-brand-600/20 border border-brand-500/30 flex items-center justify-center group-hover:shadow-glow transition-shadow">
              <Activity className="w-5 h-5 text-brand-400" />
            </div>
            <span className="text-lg font-bold text-slate-100">Clinexa</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                id={`nav-${label.toLowerCase().replace(" ", "-")}`}
                className={active ? "nav-link-active" : "nav-link"}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span className="text-sm">{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        <div className="border-t border-surface-border px-3 py-4 space-y-1">
          <div className="px-4 py-2.5 rounded-xl bg-surface-elevated">
            <p className="text-xs font-medium text-slate-300 truncate">
              {user?.user_metadata?.full_name || "User"}
            </p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
          <button
            id="nav-signout"
            onClick={signOut}
            className="nav-link w-full text-left text-red-400 hover:bg-red-500/10 hover:text-red-300"
          >
            <LogOut className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm">Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
