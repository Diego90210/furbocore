interface Stat {
  season: string;
  team: string;
  minutes_played: number;
  goals: number;
  assists: number;
  age_at_season: number;
}

interface Value {
  real_value_eur: number | null;
  predicted_value_eur: number | null;
  value_gap_pct: number | null;
}

function formatEur(value: number | null) {
  if (value === null || value === undefined) return "Sin dato";
  if (value >= 1_000_000) return `€${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `€${(value / 1_000).toFixed(0)}K`;
  return `€${value.toLocaleString("es-ES")}`;
}

function GapIndicator({ gap }: { gap: number | null }) {
  if (gap === null || gap === undefined) return null;

  let label: string;
  let color: string;

  if (gap > 15) {
    label = "Infravalorado";
    color = "text-emerald-700 bg-emerald-50 border border-emerald-200";
  } else if (gap < -15) {
    label = "Sobrevalorado";
    color = "text-rose-700 bg-rose-50 border border-rose-200";
  } else {
    label = "Alineado";
    color = "text-slate-600 bg-slate-50 border border-slate-200";
  }

  return (
    <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${color}`}>
      {label} ({gap > 0 ? "+" : ""}
      {gap.toFixed(1)}%)
    </span>
  );
}

export default function PlayerCard({
  stats,
  value,
}: {
  stats: Stat[];
  value: Value | null;
}) {
  if (!stats.length) {
    return (
      <div className="mt-6 p-6 bg-white rounded-2xl shadow-sm border border-slate-200/60 text-center text-slate-400">
        No hay estadisticas disponibles para este jugador.
      </div>
    );
  }

  return (
    <div className="mt-6 space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 p-6">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Valoracion de Mercado
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div>
            <div className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-1">
              Valor Real
            </div>
            <div className="text-2xl font-bold text-slate-800">
              {formatEur(value?.real_value_eur ?? null)}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-1">
              Valor Predicho
            </div>
            <div className="text-2xl font-bold text-blue-600">
              {formatEur(value?.predicted_value_eur ?? null)}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-1">
              Evaluacion
            </div>
            <div className="mt-1">
              <GapIndicator gap={value?.value_gap_pct ?? null} />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 overflow-hidden">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider p-6 pb-4">
          Historial por Temporada
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-t border-slate-100">
              <tr>
                <th className="px-6 py-3 text-left font-semibold text-slate-500 text-xs uppercase tracking-wider">
                  Temporada
                </th>
                <th className="px-6 py-3 text-left font-semibold text-slate-500 text-xs uppercase tracking-wider">
                  Equipo
                </th>
                <th className="px-6 py-3 text-right font-semibold text-slate-500 text-xs uppercase tracking-wider">
                  Minutos
                </th>
                <th className="px-6 py-3 text-right font-semibold text-slate-500 text-xs uppercase tracking-wider">
                  Goles
                </th>
                <th className="px-6 py-3 text-right font-semibold text-slate-500 text-xs uppercase tracking-wider">
                  Asist.
                </th>
                <th className="px-6 py-3 text-right font-semibold text-slate-500 text-xs uppercase tracking-wider">
                  Edad
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {stats.map((row, i) => (
                <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-3 font-medium text-slate-700">{row.season}</td>
                  <td className="px-6 py-3 text-slate-600">{row.team}</td>
                  <td className="px-6 py-3 text-right text-slate-600">
                    {row.minutes_played.toLocaleString()}
                  </td>
                  <td className="px-6 py-3 text-right font-semibold text-slate-800">
                    {row.goals}
                  </td>
                  <td className="px-6 py-3 text-right font-semibold text-slate-800">
                    {row.assists}
                  </td>
                  <td className="px-6 py-3 text-right text-slate-500">
                    {row.age_at_season ?? "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
