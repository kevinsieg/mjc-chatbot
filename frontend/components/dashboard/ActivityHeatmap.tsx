import type { HeatmapPoint } from "@/lib/types"

interface Props {
  data: HeatmapPoint[]
  panelClass?: string
  titleClass?: string
}

// Monday-first display order; maps display row → PostgreSQL DOW value
const DAY_ORDER = [1, 2, 3, 4, 5, 6, 0]
const DAY_LABELS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
const HOURS = Array.from({ length: 24 }, (_, i) => i)

export default function ActivityHeatmap({ data, panelClass, titleClass }: Props) {
  const lookup = new Map(data.map((p) => [`${p.day}-${p.hour}`, p.count]))
  const max = Math.max(...data.map((p) => p.count), 1)

  function cellColor(count: number): string {
    if (count === 0) return "#f1f5f9"
    const intensity = count / max
    // interpolate white→#2563eb
    const r = Math.round(255 - intensity * (255 - 37))
    const g = Math.round(255 - intensity * (255 - 99))
    const b = Math.round(255 - intensity * (255 - 235))
    return `rgb(${r},${g},${b})`
  }

  return (
    <div className={panelClass}>
      <h2 className={titleClass}>Activité par jour et heure</h2>
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "separate", borderSpacing: 3, fontSize: "0.75rem", minWidth: 560 }}>
          <thead>
            <tr>
              <th style={{ width: 36 }} />
              {HOURS.map((h) => (
                <th
                  key={h}
                  style={{
                    width: 22,
                    textAlign: "center",
                    color: "#94a3b8",
                    fontWeight: 400,
                    paddingBottom: 4,
                  }}
                >
                  {h % 3 === 0 ? `${h}h` : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {DAY_ORDER.map((dow, i) => (
              <tr key={dow}>
                <td
                  style={{
                    textAlign: "right",
                    paddingRight: 8,
                    color: "#64748b",
                    fontWeight: 500,
                    whiteSpace: "nowrap",
                  }}
                >
                  {DAY_LABELS[i]}
                </td>
                {HOURS.map((h) => {
                  const count = lookup.get(`${dow}-${h}`) ?? 0
                  return (
                    <td
                      key={h}
                      title={count > 0 ? `${DAY_LABELS[i]} ${h}h — ${count} msg` : undefined}
                      style={{
                        width: 22,
                        height: 18,
                        borderRadius: 3,
                        backgroundColor: cellColor(count),
                        cursor: count > 0 ? "default" : undefined,
                      }}
                    />
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 10, fontSize: "0.6875rem", color: "#94a3b8" }}>
          <span>Moins</span>
          {[0, 0.25, 0.5, 0.75, 1].map((v) => (
            <span
              key={v}
              style={{ width: 12, height: 12, borderRadius: 2, backgroundColor: cellColor(Math.round(v * max)), display: "inline-block" }}
            />
          ))}
          <span>Plus</span>
        </div>
      </div>
    </div>
  )
}
