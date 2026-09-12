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
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${value * 100}%` }}
        />
      </div>
      <span className="text-sm font-semibold w-14 text-right text-slate-700">
        {(value * 100).toFixed(1)}%
      </span>
    </div>
  );
}

function FormBadges({ form }: { form: string }) {
  if (!form) return <span className="text-slate-400 text-xs">Sin datos</span>;
  return (
    <div className="flex gap-0.5">
      {form.split("-").map((r, i) => {
        const bg =
          r === "W" ? "bg-emerald-500" : r === "D" ? "bg-amber-400" : "bg-rose-500";
        return (
          <span
            key={i}
            className={`${bg} text-white text-xs w-6 h-6 flex items-center justify-center rounded-md font-medium`}
          >
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
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 p-6 hover:shadow-md transition-shadow duration-200">
      <div className="text-xs font-medium text-slate-400 mb-3 uppercase tracking-wider">
        {date}
      </div>

      <div className="flex items-center justify-between mb-5">
        <div className="text-lg font-bold flex-1 text-slate-800">{match.home_team}</div>
        <div className="text-slate-300 mx-4 text-sm font-medium">VS</div>
        <div className="text-lg font-bold flex-1 text-right text-slate-800">
          {match.away_team}
        </div>
      </div>

      {pred ? (
        <>
          <div className="space-y-2.5 mb-5">
            <div className="flex items-center gap-3">
              <span className="text-sm text-slate-500 w-20 font-medium">Local</span>
              <ProbBar value={pred.home_win_prob} color="bg-blue-500" />
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-slate-500 w-20 font-medium">Empate</span>
              <ProbBar value={pred.draw_prob} color="bg-slate-400" />
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-slate-500 w-20 font-medium">Visitante</span>
              <ProbBar value={pred.away_win_prob} color="bg-orange-500" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm border-t border-slate-100 pt-4">
            <div>
              <div className="text-slate-400 mb-1.5 text-xs font-medium uppercase tracking-wider">
                Forma Local
              </div>
              <FormBadges form={pred.home_form_summary} />
            </div>
            <div className="text-right">
              <div className="text-slate-400 mb-1.5 text-xs font-medium uppercase tracking-wider">
                Forma Visitante
              </div>
              <FormBadges form={pred.away_form_summary} />
            </div>
          </div>
        </>
      ) : (
        <p className="text-sm text-slate-400 text-center py-4">
          Prediccion no disponible aun.
        </p>
      )}
    </div>
  );
}
