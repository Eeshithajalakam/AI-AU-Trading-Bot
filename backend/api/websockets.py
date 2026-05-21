# pyrefly: ignore [missing-import]
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
import time
import uuid
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import List

from ai.service import AIService
from trading.order_manager import OrderManager

# Initialize AI Service
ai_service = AIService()

# Initialize Order Manager
order_manager = OrderManager()

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

async def market_data_broadcaster():
    current_price = 2350.00
    history = []
    
    # Pre-fill history with dummy data to satisfy the 50-period AI requirement
    p = current_price
    now = datetime.utcnow()
    for i in range(100, 0, -1):
        t = now - timedelta(seconds=i)
        p += (random.random() - 0.5) * 2.0
        history.append({
            "timestamp": t,
            "open": p - 0.5,
            "high": p + 1.0,
            "low": p - 1.0,
            "close": p,
            "volume": random.random() * 100
        })

    loop_count = 0
    while True:
        try:
            # 1. Update Price and History (Always Runs)
            current_price += (random.random() - 0.48) * 2.0
            now = datetime.utcnow()
            
            # Update history
            history.append({
                "timestamp": now,
                "open": current_price - 0.5,
                "high": current_price + 1.0,
                "low": current_price - 1.0,
                "close": current_price,
                "volume": random.random() * 100
            })
            # Keep last 100 items
            if len(history) > 100:
                history.pop(0)

            # Broadcast Price Update if clients exist
            if manager.active_connections:
                price_msg = json.dumps({
                    "type": "PRICE_UPDATE",
                    "price": round(current_price, 2),
                    "timestamp": now.isoformat()
                })
                await manager.broadcast(price_msg)

            # 2. Generate AI Signal every 10 seconds (Always Runs)
            if loop_count % 10 == 0:
                print("Generating AI signal...")
                df = pd.DataFrame(history).set_index("timestamp")
                
                try:
                    ai_result = await ai_service.analyze_market_data(df)
                    
                    signal_type = "LONG" if ai_result["action"] == "BUY" else "SHORT" if ai_result["action"] == "SELL" else "NEUTRAL"
                    
                    if signal_type != "NEUTRAL":
                        print(f"Signal generated successfully: {signal_type} at {current_price}")
                        # Create a frontend-compatible signal payload
                        signal_payload = {
                            "id": f"ai-sig-{uuid.uuid4().hex[:6]}",
                            "type": signal_type,
                            "asset": "XAU/USD",
                            "confidence": ai_result["confidence_score"],
                            "entry": current_price,
                            "target": ai_result["predicted_price"],
                            "stopLoss": current_price * 0.995 if signal_type == "LONG" else current_price * 1.005,
                            "timestamp": int(now.timestamp() * 1000),
                            "active": True
                        }
                        
                        # Broadcast if clients exist
                        if manager.active_connections:
                            signal_msg = json.dumps({
                                "type": "SIGNAL_UPDATE",
                                "signals": [signal_payload]
                            })
                            await manager.broadcast(signal_msg)
                            
                            notify_msg = json.dumps({
                                "type": "NOTIFICATION",
                                "title": f"AI Signal: {signal_type}",
                                "message": f"{signal_payload['asset']} Target: {signal_payload['target']}",
                                "level": "INFO"
                            })
                            await manager.broadcast(notify_msg)
                        
                        # Execute Trade Automatically!
                        print(f"Executing trade for {signal_type}...")
                        # Run MT5 synchronous execution in a background thread to prevent blocking WebSocket loop
                        trade_result = await asyncio.to_thread(
                            order_manager.process_signal, signal_payload, 0.01
                        )
                        print(f"Trade Execution Result: {trade_result}")
                    else:
                        print("AI Signal: NEUTRAL (no trade)")
                except Exception as e:
                    import traceback
                    print(f"AI Service Error:\n{traceback.format_exc()}")

            loop_count += 1
                
        except Exception as e:
            import traceback
            print(f"Broadcaster error:\n{traceback.format_exc()}")
            
        await asyncio.sleep(1.0) # Broadcast every 1 second

@router.websocket("/ws/trading")
async def websocket_trading_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send initial data
    import random
    from datetime import datetime, timedelta
    
    # Mock history
    history = []
    p = 2350.00
    now = datetime.utcnow()
    for i in range(60, 0, -1):
        t = now - timedelta(seconds=i)
        p += (random.random() - 0.48) * 1.5
        history.append({
            "time": t.isoformat(),
            "price": round(p, 2)
        })
        
    initial_signals = [
        {
            "id": "sig-1", "type": "LONG", "asset": "XAU/USD",
            "confidence": 94, "entry": 2345.50, "target": 2360.00,
            "stopLoss": 2335.00, "timestamp": int(time.time() * 1000), "active": True
        }
    ]
    
    await websocket.send_text(json.dumps({
        "type": "INITIAL_DATA",
        "history": history,
        "signals": initial_signals
    }))
    
    try:
        while True:
            # Keep connection alive, listen for client messages if any
            data = await websocket.receive_text()
            print(f"Received from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket Error: {e}")
        manager.disconnect(websocket)
