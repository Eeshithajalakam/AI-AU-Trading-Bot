import { create } from 'zustand';
import { toast } from 'react-hot-toast';

export interface PricePoint {
  time: string;
  price: number;
}

export interface CandlePoint {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface TradeSignal {
  id: string;
  type: "LONG" | "SHORT" | "NEUTRAL";
  action?: string;
  asset: string;
  confidence: number;
  entry: number;
  target: number;
  stopLoss: number;
  timestamp: number;
  active: boolean;
  trend?: string;
}

export interface TrainingState {
  job_id?: number | null;
  status: string;
  progress_pct: number;
  current_epoch?: number;
  total_epochs?: number;
  train_loss?: number | null;
  val_mae?: number | null;
  val_rmse?: number | null;
  directional_accuracy?: number | null;
  message?: string;
}

export interface RiskState {
  daily_pnl: number;
  daily_trades: number;
  emergency_shutdown: boolean;
  account?: {
    balance?: number;
    equity?: number;
    profit?: number;
    paper?: boolean;
  };
  paper_mode?: boolean;
  auto_trade?: boolean;
}

interface TradingStore {
  isConnected: boolean;
  setIsConnected: (status: boolean) => void;
  reconnectAttempts: number;
  currentPrice: number;
  priceHistory: PricePoint[];
  candles: CandlePoint[];
  signals: TradeSignal[];
  training: TrainingState | null;
  risk: RiskState | null;
  lastTrade: Record<string, unknown> | null;
  updatePrice: (price: number, timestamp: string, ohlcv?: CandlePoint) => void;
  setInitialHistory: (history: PricePoint[], candles?: CandlePoint[]) => void;
  updateSignals: (signals: TradeSignal[]) => void;
  setTraining: (t: TrainingState) => void;
  setRisk: (r: RiskState) => void;
  setLastTrade: (t: Record<string, unknown>) => void;
  connectWebSocket: (url: string) => void;
  disconnectWebSocket: () => void;
}

let wsInstance: WebSocket | null = null;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
let pingInterval: ReturnType<typeof setInterval> | null = null;
const MAX_HISTORY_POINTS = 120;

export const useTradingStore = create<TradingStore>((set, get) => ({
  isConnected: false,
  reconnectAttempts: 0,
  setIsConnected: (status) => set({ isConnected: status }),

  currentPrice: 2350.0,
  priceHistory: [],
  candles: [],
  signals: [],
  training: null,
  risk: null,
  lastTrade: null,

  updatePrice: (price, timestamp, ohlcv) => set((state) => {
    const newHistory = [...state.priceHistory, { time: timestamp, price }];
    if (newHistory.length > MAX_HISTORY_POINTS) newHistory.shift();
    let newCandles = state.candles;
    if (ohlcv) {
      newCandles = [...state.candles, ohlcv];
      if (newCandles.length > MAX_HISTORY_POINTS) newCandles.shift();
    }
    return { currentPrice: price, priceHistory: newHistory, candles: newCandles };
  }),

  setInitialHistory: (history, candles) => set({
    priceHistory: history,
    candles: candles || [],
    currentPrice: history[history.length - 1]?.price || 2350.0,
  }),

  updateSignals: (newSignals) => set((state) => {
    newSignals.forEach((newSig) => {
      const oldSig = state.signals.find((s) => s.id === newSig.id);
      if (newSig.active && newSig.confidence >= 55 && (!oldSig || oldSig.confidence < 55)) {
        toast.success(`AI ${newSig.type}: ${newSig.asset} @ ${newSig.entry}`);
      }
    });
    return { signals: newSignals };
  }),

  setTraining: (training) => set({ training }),
  setRisk: (risk) => set({ risk }),
  setLastTrade: (lastTrade) => set({ lastTrade }),

  connectWebSocket: (url: string) => {
    if (wsInstance) wsInstance.close();
    if (reconnectTimeout) clearTimeout(reconnectTimeout);
    if (pingInterval) clearInterval(pingInterval);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        set({ isConnected: true, reconnectAttempts: 0 });
        toast.success('Live feed connected');
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping');
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          switch (data.type) {
            case 'PRICE_UPDATE':
              get().updatePrice(data.price, data.timestamp, data.ohlcv);
              break;
            case 'SIGNAL_UPDATE':
              get().updateSignals(data.signals);
              break;
            case 'INITIAL_DATA':
              get().setInitialHistory(data.history, data.candles);
              if (data.price) set({ currentPrice: data.price });
              if (data.signals?.length) get().updateSignals(data.signals);
              if (data.training) get().setTraining(data.training);
              if (data.account) get().setRisk({ daily_pnl: 0, daily_trades: 0, emergency_shutdown: false, account: data.account });
              break;
            case 'TRAINING_UPDATE':
              get().setTraining(data.training);
              break;
            case 'RISK_UPDATE':
              get().setRisk({
                daily_pnl: data.daily_pnl,
                daily_trades: data.daily_trades,
                emergency_shutdown: data.emergency_shutdown,
                account: data.account,
                paper_mode: data.paper_mode,
                auto_trade: data.auto_trade,
              });
              break;
            case 'TRADE_UPDATE':
              get().setLastTrade(data.trade);
              if (data.trade?.status === 'success') toast.success('Trade executed');
              break;
            case 'NOTIFICATION':
              toast(`${data.title}: ${data.message}`);
              break;
          }
        } catch (err) {
          console.error('WS parse error', err);
        }
      };

      ws.onclose = () => {
        set({ isConnected: false });
        if (pingInterval) clearInterval(pingInterval);
        const attempts = get().reconnectAttempts;
        const delay = Math.min(1000 * Math.pow(2, attempts), 30000);
        set({ reconnectAttempts: attempts + 1 });
        reconnectTimeout = setTimeout(() => get().connectWebSocket(url), delay);
      };

      ws.onerror = () => console.error('WebSocket error');
      wsInstance = ws;
    } catch (e) {
      console.error('WS connect failed', e);
    }
  },

  disconnectWebSocket: () => {
    if (pingInterval) clearInterval(pingInterval);
    if (reconnectTimeout) clearTimeout(reconnectTimeout);
    if (wsInstance) { wsInstance.close(); wsInstance = null; }
  },
}));
