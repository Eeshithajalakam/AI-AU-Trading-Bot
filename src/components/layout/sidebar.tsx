import { Activity, BarChart3, Clock, History, LayoutDashboard, Settings, TrendingUp, Wallet } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard, current: true },
  { name: "Markets", href: "#", icon: BarChart3, current: false },
  { name: "Backtesting", href: "/backtest", icon: History, current: false },
  { name: "AI Signals", href: "#", icon: Activity, current: false },
  { name: "Analytics", href: "#", icon: TrendingUp, current: false },
];

export function Sidebar() {
  return (
    <div className="flex h-full w-64 flex-col border-r border-white/5 bg-[#0a0a0c]/80 backdrop-blur-xl">
      <div className="flex h-16 items-center px-6 border-b border-white/5">
        <div className="flex items-center gap-2 text-amber-500">
          <Activity className="h-6 w-6" />
          <span className="text-lg font-bold tracking-tight text-white">Au<span className="text-amber-500">Trade</span> AI</span>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              item.current
                ? "bg-white/10 text-white"
                : "text-slate-400 hover:bg-white/5 hover:text-white",
              "group flex items-center rounded-md px-3 py-2.5 text-sm font-medium transition-colors"
            )}
          >
            <item.icon
              className={cn(
                item.current ? "text-amber-500" : "text-slate-500 group-hover:text-amber-500",
                "mr-3 h-5 w-5 flex-shrink-0 transition-colors"
              )}
              aria-hidden="true"
            />
            {item.name}
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-white/5">
        <Link
          href="#"
          className="group flex items-center rounded-md px-3 py-2.5 text-sm font-medium text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
        >
          <Settings className="mr-3 h-5 w-5 text-slate-500 group-hover:text-slate-300 transition-colors" />
          Settings
        </Link>
        <div className="mt-4 flex items-center gap-3 px-3">
          <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center text-xs font-bold text-white shadow-lg">
            JD
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-medium text-white">Pro Trader</span>
            <span className="text-[10px] text-emerald-400 flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Connected
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
