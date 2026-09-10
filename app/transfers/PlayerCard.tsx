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
  return `€${value.toLocaleString("es-ES")}`;
}

function GapIndicator({ gap }: { gap: number | null }) {
  if (gap === null || gap === undefined) return null;

  let label: string;
  let color: string;

  if (gap > 15) {
    label = "Infravalorado";
    color = "text-green-600 bg-green-50";
  } else if (gap < -15) {
    label = "Sobrevalorado";
    color = "text-red-600 bg-red-50";
  } else {
    label = "Alineado con el mercado";
    color = "text-gray-600 bg-gray-50";
  }

  return (
    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${color}`}>
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
      <div className="mt-6 p-6 bg-white rounded-lg shadow text-center text-gray-500">
        No stats available for this player.
      </div>
    );
  }

  return (
    <div className="mt-6 space-y-6">
      {/* Value Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Transfer Valuation</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-gray-500">Real Value</div>
            <div className="text-2xl font-bold">{formatEur(value?.real_value_eur ?? null)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Predicted Value</div>
            <div className="text-2xl font-bold">{formatEur(value?.predicted_value_eur ?? null)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Assessment</div>
            <div className="mt-1">
              <GapIndicator gap={value?.value_gap_pct ?? null} />
            </div>
          </div>
        </div>
      </div>

      {/* Stats Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <h2 className="text-xl font-semibold p-6 pb-4">Season History</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-t">
              <tr>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Season</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500">Team</th>
                <th className="px-6 py-3 text-right font-medium text-gray-500">Minutes</th>
                <th className="px-6 py-3 text-right font-medium text-gray-500">Goals</th>
                <th className="px-6 py-3 text-right font-medium text-gray-500">Assists</th>
                <th className="px-6 py-3 text-right font-medium text-gray-500">Age</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {stats.map((row, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-6 py-3">{row.season}</td>
                  <td className="px-6 py-3">{row.team}</td>
                  <td className="px-6 py-3 text-right">{row.minutes_played.toLocaleString()}</td>
                  <td className="px-6 py-3 text-right">{row.goals}</td>
                  <td className="px-6 py-3 text-right">{row.assists}</td>
                  <td className="px-6 py-3 text-right">{row.age_at_season ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
