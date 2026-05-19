"use client";

import { useEffect } from "react";
import { useTradingStore } from "@/store/useTradingStore";

export function WebSocketManager() {
  const connectWebSocket = useTradingStore((state) => state.connectWebSocket);
  const disconnectWebSocket = useTradingStore((state) => state.disconnectWebSocket);

  useEffect(() => {
    // Connect to our mock local websocket server for now
    connectWebSocket("ws://localhost:8080");

    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]);

  return null; // This component doesn't render anything
}
