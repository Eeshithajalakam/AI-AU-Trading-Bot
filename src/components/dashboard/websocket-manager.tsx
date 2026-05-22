"use client";

import { useEffect } from "react";
import { useTradingStore } from "@/store/useTradingStore";
import { getWsUrl } from "@/lib/api";

export function WebSocketManager() {
  const connectWebSocket = useTradingStore((state) => state.connectWebSocket);
  const disconnectWebSocket = useTradingStore((state) => state.disconnectWebSocket);

  useEffect(() => {
    connectWebSocket(getWsUrl("/ws/trading"));
    return () => disconnectWebSocket();
  }, [connectWebSocket, disconnectWebSocket]);

  return null;
}
