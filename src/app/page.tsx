import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { MarketOverview } from "@/components/dashboard/market-overview";
import { AISignals } from "@/components/dashboard/ai-signals";
import { TradeHistory } from "@/components/dashboard/trade-history";
import { RiskMetrics } from "@/components/dashboard/risk-metrics";
import { WebSocketManager } from "@/components/dashboard/websocket-manager";

export default function Dashboard() {
  return (
    <div className="flex h-screen overflow-hidden bg-[#0a0a0c]">
      <WebSocketManager />
      
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-amber-500/5 blur-[120px]" />
        <div className="absolute top-[60%] -right-[10%] w-[40%] h-[40%] rounded-full bg-indigo-500/5 blur-[120px]" />
      </div>

      {/* App Layout */}
      <div className="relative z-10 flex h-full w-full">
        <Sidebar />
        
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header />
          
          <main className="flex-1 overflow-y-auto p-6 scroll-smooth">
            <div className="mx-auto max-w-7xl space-y-6">
              
              {/* Top Row: Chart and Signals */}
              <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
                <MarketOverview />
                <AISignals />
              </div>
              
              {/* Bottom Row: Trades and Analytics */}
              <div className="grid grid-cols-1 gap-6 xl:grid-cols-12 pb-6">
                <TradeHistory />
                <RiskMetrics />
              </div>
              
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
