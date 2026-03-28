"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { SystemMetricsPayload } from "@/types/system-metrics";

type SystemUsageChartProps = {
  samples: SystemMetricsPayload[];
};

export function SystemUsageChart({ samples }: SystemUsageChartProps) {
  const data = samples.map((s, idx) => ({
    t: idx,
    cpu: s.cpu,
    ram: s.ram,
    gpu: s.gpu,
    vram: s.vram,
  }));

  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="hsl(217 19% 18%)" strokeDasharray="3 3" />
          <XAxis dataKey="t" tick={false} height={8} />
          <YAxis domain={[0, 100]} width={32} tick={{ fill: "hsl(215 16% 65%)", fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              background: "hsl(222 14% 11%)",
              border: "1px solid hsl(217 19% 18%)",
              borderRadius: 8,
            }}
            labelStyle={{ color: "hsl(210 20% 96%)", fontSize: 12 }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: "hsl(215 16% 65%)" }} />
          <Line type="monotone" dataKey="cpu" name="CPU" stroke="hsl(217 91% 60%)" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="ram" name="RAM" stroke="hsl(142 70% 45%)" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="gpu" name="GPU" stroke="hsl(280 85% 65%)" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="vram" name="VRAM" stroke="hsl(38 92% 55%)" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
