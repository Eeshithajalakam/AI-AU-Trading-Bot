import { create } from 'zustand';
import { toast } from 'react-hot-toast';

export interface PricePoint {
  time: string;
  price: number;
}

export interface TradeSignal {
  id: string;
  type: "LONG" | "SHORT";
  asset: string;
  confidence: number;
  entry: number;
  target: number;
  stopLoss: number;
  timestamp: number;
  active: boolean;
}

interface TradingStore {
  // Connection State
  isConnected: boolean;
  setIsConnected: (status: boolean) => void;
  reconnectAttempts: number;
  
  // Market Data
  currentPrice: number;
  priceHistory: PricePoint[];
  updatePrice: (price: number, timestamp: string) => void;
  setInitialHistory: (history: PricePoint[]) => void;
  
  // Signals
  signals: TradeSignal[];
  updateSignals: (signals: TradeSignal[]) => void;
  
  // WS Methods
  connectWebSocket: (url: string) => void;
  disconnectWebSocket: () => void;
}

let wsInstance: WebSocket | null = null;
let reconnectTimeout: NodeJS.Timeout | null = null;
const MAX_HISTORY_POINTS = 60; // Keep last 60 data points

export const useTradingStore = create<TradingStore>((set, get) => ({
  isConnected: false,
  reconnectAttempts: 0,
  setIsConnected: (status) => set({ isConnected: status }),
  
  currentPrice: 2350.00,
  priceHistory: [],
  
  updatePrice: (price, timestamp) => set((state) => {
    const newPoint = { time: timestamp, price };
    const newHistory = [...state.priceHistory, newPoint];
    if (newHistory.length > MAX_HISTORY_POINTS) {
      newHistory.shift();
    }
    return { 
      currentPrice: price, 
      priceHistory: newHistory 
    };
  }),
  
  setInitialHistory: (history) => set({ priceHistory: history, currentPrice: history[history.length - 1]?.price || 2350.00 }),
  
  signals: [],
  updateSignals: (newSignals) => set((state) => {
    // Check for high confidence signals to trigger notifications
    newSignals.forEach(newSig => {
      const oldSig = state.signals.find(s => s.id === newSig.id);
      // Lowered threshold to 55 since we updated the backend confidence scoring
      if (newSig.active && newSig.confidence >= 55 && (!oldSig || oldSig.confidence < 55)) {
        toast.success(`AI ${newSig.type} Signal: ${newSig.asset} @ ${newSig.entry}`, {
          duration: 5000,
          position: 'top-right',
          style: {
            background: '#1f1f23',
            color: '#ededed',
            border: '1px solid rgba(16, 185, 129, 0.2)',
          },
          iconTheme: {
            primary: '#10b981',
            secondary: '#1f1f23',
          },
        });
        
        // Native Browser Push Notification
        if (typeof window !== 'undefined' && 'Notification' in window) {
          if (Notification.permission === 'granted') {
            new Notification(`AuTrade AI: ${newSig.type} Signal`, {
              body: `${newSig.asset} Entry: ${newSig.entry} (Conf: ${newSig.confidence}%)`,
            });
          }
        }
      }
    });

    return { signals: newSignals };
  }),
  
  connectWebSocket: (url: string) => {
    if (wsInstance) {
      wsInstance.close();
    }
    
    // Clear any pending reconnects
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    
    try {
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        console.log('WebSocket Connected');
        set({ isConnected: true, reconnectAttempts: 0 });
        toast.success('Live trading feed connected', {
          position: 'bottom-right',
          style: { background: '#1f1f23', color: '#ededed', border: '1px solid rgba(255,255,255,0.1)' }
        });
        
        // Request Browser Push Notification Permission
        if (typeof window !== 'undefined' && 'Notification' in window) {
          if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
            Notification.requestPermission();
          }
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'PRICE_UPDATE') {
            get().updatePrice(data.price, data.timestamp);
          } else if (data.type === 'SIGNAL_UPDATE') {
            get().updateSignals(data.signals);
          } else if (data.type === 'INITIAL_DATA') {
            get().setInitialHistory(data.history);
            get().updateSignals(data.signals);
          } else if (data.type === 'NOTIFICATION') {
            const { title, message, level } = data;
            
            // Toast
            if (level === "CRITICAL" || level === "ERROR") toast.error(`${title}\n${message}`);
            else if (level === "SUCCESS") toast.success(`${title}\n${message}`);
            else toast(`${title}\n${message}`, { style: { background: '#1f1f23', color: '#fff' }});
            
            // Native Push
            if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') {
               new Notification(title, { body: message });
            }
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message', err);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket Disconnected');
        set({ isConnected: false });
        
        // Auto-reconnect with exponential backoff
        const attempts = get().reconnectAttempts;
        const delay = Math.min(1000 * Math.pow(2, attempts), 30000); // max 30s delay
        
        console.log(`Attempting reconnect in ${delay}ms (Attempt ${attempts + 1})`);
        if (attempts === 0) {
          toast.error('Connection lost. Attempting to reconnect...', {
            position: 'bottom-right',
            style: { background: '#1f1f23', color: '#ededed', border: '1px solid rgba(239, 68, 68, 0.2)' }
          });
        }
        
        set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 }));
        
        reconnectTimeout = setTimeout(() => {
          get().connectWebSocket(url);
        }, delay);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket Error:', error);
      };
      
      wsInstance = ws;
    } catch (error) {
      console.error('WebSocket Connection Failed:', error);
    }
  },
  
  disconnectWebSocket: () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    if (wsInstance) {
      wsInstance.close();
      wsInstance = null;
    }
  }
}));
