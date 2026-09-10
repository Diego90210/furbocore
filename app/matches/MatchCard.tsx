interface Match {
  id: string;
  home_team: string;
  away_team: string;
  match_date: string;
  home_goals: number | null;
  away_goals: number | null;
  prediction: {
    home_win_prob: number;
    draw_prob: number;
    away_win_prob: number;
    elo_home: number | null;
    elo_away: number | null;
    home_form_summary: string;
    away_form_summary: string;
  } | null;
}

function ProbBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded-full h-2.5">
        <div className={`h-2.5 rounded-full ${color}`} style={{ width: `${value * 100}%` }} />
      </div>
      <span className="text-sm font-medium w-12 text-right">{(value * 100).toFixed(1)}%</span>
    </div>
  );
}

function FormBadges({ form }: { form: string }) {
  if (!form) return <span className="text-gray-400 text-xs">No data</span>;
  return (
    <div className="flex gap-0.5">
      {form.split("-").map((r, i) => {
        const bg =
          r === "W" ? "bg-green-500" : r === "D" ? "bg-yellow-400" : "bg-red-500";
        return (
          <span key={i} className={`${bg} text-white text-xs w-5 h-5 flex items-center justify-center rounded`}>
            {r}
          </span>
        );
      })}
    </div>
  );
}

export default function MatchCard({ match }: { match: Match }) {
  const pred = match.prediction;
  const date = new Date(match.match_date).toLocaleDateString("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return (
    <div className="bg-white rounded-lg shadow p-5">
      {/* Date */}
      <div className="text-sm text-gray-500 mb-3">{date}</div>

      {/* Teams */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-lg font-semibold flex-1">{match.home_team}</div>
        <div className="text-gray-400 mx-4">vs</div>
        <div className="text-lg font-semibold flex-1 text-right">{match.away_team}</div>
      </div>

      {pred ? (
        <>
          {/* Probabilities */}
          <div className="space-y-2 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600 w-20">Home Win</span>
              <ProbBar value={pred.home_win_prob} color="bg-blue-600" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600 w-20">Draw</span>
              <ProbBar value={pred.draw_prob} color="bg-gray-500" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600 w-20">Away Win</span>
              <ProbBar value={pred.away_win_prob} color="bg-orange-500" />
            </div>
          </div>

          {/* Elo + Form */}
          <div className="grid grid-cols-2 gap-4 text-sm border-t pt-3">
            <div>
              <div className="text-gray-500 mb-1">Home Form</div>
              <FormBadges form={pred.home_form_summary} />
            </div>
            <div className="text-right">
              <div className="text-gray-500 mb-1">Away Form</div>
              <FormBadges form={pred.away_form_summary} />
            </div>
          </div>
        </>
      ) : (
        <p className="text-sm text-gray-400 text-center py-4">No prediction available yet.</p>
      )}
    </div>
  );
}
