import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { BacktestEngineUI } from "@/components/dashboard/backtest-engine-ui";

export default function BacktestPage() {
  return (
    <div className="flex h-screen overflow-hidden bg-[#0a0a0c]">
      
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-indigo-500/5 blur-[120px]" />
        <div className="absolute top-[60%] -right-[10%] w-[40%] h-[40%] rounded-full bg-purple-500/5 blur-[120px]" />
      </div>

      {/* App Layout */}
      <div className="relative z-10 flex h-full w-full">
        <Sidebar />
        
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header />
          
          <main className="flex-1 overflow-y-auto p-6 scroll-smooth">
            <div className="mx-auto max-w-7xl">
              <BacktestEngineUI />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
