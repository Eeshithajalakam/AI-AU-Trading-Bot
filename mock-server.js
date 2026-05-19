const { WebSocketServer } = require('ws');

const wss = new WebSocketServer({ port: 8080 });

console.log("Mock WebSocket Server running on ws://localhost:8080");

// Generate initial history
const generateHistory = () => {
  const data = [];
  let price = 2350.00;
  const now = new Date();
  
  for (let i = 60; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 1000); // 1 point per second for last 60s
    price = price + (Math.random() - 0.48) * 1.5;
    data.push({
      time: time.toISOString(),
      price: Number(price.toFixed(2)),
    });
  }
  return data;
};

let currentPrice = 2350.00;
let baseSignals = [
  {
    id: "sig-1",
    type: "LONG",
    asset: "XAU/USD",
    confidence: 94,
    entry: 2345.50,
    target: 2360.00,
    stopLoss: 2335.00,
    timestamp: Date.now() - 120000,
    active: true,
  },
  {
    id: "sig-2",
    type: "SHORT",
    asset: "XAU/USD",
    confidence: 82,
    entry: 2355.20,
    target: 2340.00,
    stopLoss: 2362.00,
    timestamp: Date.now() - 2700000,
    active: false,
  }
];

wss.on('connection', function connection(ws) {
  console.log("New client connected!");
  
  // Send initial data snapshot
  ws.send(JSON.stringify({
    type: 'INITIAL_DATA',
    history: generateHistory(),
    signals: baseSignals
  }));

  // Setup interval to simulate real-time price updates (every 1 second)
  const priceInterval = setInterval(() => {
    // Random walk for price
    currentPrice = currentPrice + (Math.random() - 0.48) * 2.0;
    
    ws.send(JSON.stringify({
      type: 'PRICE_UPDATE',
      price: Number(currentPrice.toFixed(2)),
      timestamp: new Date().toISOString()
    }));
  }, 1000);

  // Setup interval to simulate signal changes (every 15 seconds)
  const signalInterval = setInterval(() => {
    // Randomize confidence to simulate live model analysis
    const updatedSignals = baseSignals.map(sig => {
      if (sig.active) {
        let newConf = sig.confidence + Math.floor((Math.random() - 0.5) * 5);
        if (newConf > 99) newConf = 99;
        if (newConf < 50) newConf = 50;
        return { ...sig, confidence: newConf, timestamp: Date.now() };
      }
      return sig;
    });
    
    baseSignals = updatedSignals;
    
    ws.send(JSON.stringify({
      type: 'SIGNAL_UPDATE',
      signals: updatedSignals
    }));
  }, 15000);

  ws.on('close', () => {
    console.log("Client disconnected");
    clearInterval(priceInterval);
    clearInterval(signalInterval);
  });
});
