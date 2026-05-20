import type { TopSourceRow } from "@/lib/types"

interface Props {
  data: TopSourceRow[]
  panelClass?: string
  titleClass?: string
  emptyClass?: string
  tableClass?: string
}

export default function TopSourcesPanel({ data, panelClass, titleClass, emptyClass, tableClass }: Props) {
  return (
    <div className={panelClass}>
      <h2 className={titleClass}>Sources les plus consultées</h2>
      {data.length === 0 ? (
        <p className={emptyClass}>Aucune donnée — envoyez quelques messages d'abord.</p>
      ) : (
        <table className={tableClass}>
          <thead>
            <tr>
              <th>Source</th>
              <th style={{ textAlign: "right" }}>Requêtes</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.source}>
                <td style={{ fontFamily: "monospace", fontSize: "0.8125rem" }}>
                  {row.source}
                </td>
                <td style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                  {row.hit_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
