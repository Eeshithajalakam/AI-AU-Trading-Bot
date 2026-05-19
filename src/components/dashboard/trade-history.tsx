"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const trades = [
  { id: "TRD-8429", type: "BUY", price: 2342.10, amount: 5.5, pnl: 452.50, time: "10:42 AM", status: "CLOSED" },
  { id: "TRD-8428", type: "SELL", price: 2351.80, amount: 2.0, pnl: -120.40, time: "09:15 AM", status: "CLOSED" },
  { id: "TRD-8427", type: "BUY", price: 2348.50, amount: 10.0, pnl: 1250.00, time: "08:30 AM", status: "CLOSED" },
  { id: "TRD-8426", type: "SELL", price: 2355.20, amount: 4.5, pnl: 84.20, time: "Yesterday", status: "CLOSED" },
];

export function TradeHistory() {
  return (
    <Card className="col-span-full xl:col-span-8">
      <CardHeader>
        <CardTitle>Recent Trades</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-slate-300">
            <thead className="text-xs uppercase bg-white/5 text-slate-400">
              <tr>
                <th className="px-4 py-3 rounded-tl-lg font-medium">Order ID</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Price</th>
                <th className="px-4 py-3 font-medium">Amount (oz)</th>
                <th className="px-4 py-3 font-medium">Time</th>
                <th className="px-4 py-3 font-medium text-right rounded-tr-lg">PNL</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade, i) => (
                <tr key={trade.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-3 font-medium text-slate-400">{trade.id}</td>
                  <td className="px-4 py-3">
                    <span className={`font-semibold ${trade.type === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                      {trade.type}
                    </span>
                  </td>
                  <td className="px-4 py-3">${trade.price.toFixed(2)}</td>
                  <td className="px-4 py-3">{trade.amount.toFixed(2)}</td>
                  <td className="px-4 py-3 text-slate-500">{trade.time}</td>
                  <td className="px-4 py-3 text-right">
                    <span className={`font-medium ${trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {trade.pnl >= 0 ? '+' : ''}${Math.abs(trade.pnl).toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
