"use client"

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import type { DailyPoint } from "@/lib/types"
import { TOOLTIP_STYLE } from "@/lib/chart-constants"

interface Props {
  data: DailyPoint[]
  panelClass?: string
  titleClass?: string
}

export default function DailyTrendChart({ data, panelClass, titleClass }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    label: d.date.slice(5), // "MM-DD"
  }))

  return (
    <div className={panelClass}>
      <h2 className={titleClass}>Messages — 30 derniers jours</h2>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Line
            type="monotone"
            dataKey="count"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            name="Messages"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
