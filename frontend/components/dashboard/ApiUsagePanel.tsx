import type { ApiUsageRow } from "@/lib/types"

interface Props {
  data: ApiUsageRow[]
  panelClass?: string
  titleClass?: string
  emptyClass?: string
  tableClass?: string
}

export default function ApiUsagePanel({ data, panelClass, titleClass, emptyClass, tableClass }: Props) {
  return (
    <div className={panelClass}>
      <h2 className={titleClass}>Utilisation API</h2>
      {data.length === 0 ? (
        <p className={emptyClass}>Aucune donnée disponible.</p>
      ) : (
        <table className={tableClass}>
          <thead>
            <tr>
              <th>Modèle</th>
              <th>Tokens (prompt)</th>
              <th>Tokens (réponse)</th>
              <th>Coût (€)</th>
              <th>Latence moy.</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.model}>
                <td>{row.model}</td>
                <td>{row.prompt_tokens.toLocaleString()}</td>
                <td>{row.completion_tokens.toLocaleString()}</td>
                <td>€{row.cost_eur.toFixed(4)}</td>
                <td>{row.avg_latency_ms} ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
