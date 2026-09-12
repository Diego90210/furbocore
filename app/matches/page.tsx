import { supabase } from "@/lib/supabase";
import MatchCard from "./MatchCard";

export const revalidate = 3600;

async function getUpcomingMatches() {
  const { data: matches } = await supabase
    .from("matches")
    .select("*")
    .eq("status", "scheduled")
    .order("match_date", { ascending: true })
    .limit(10);

  if (!matches || matches.length === 0) return [];

  const matchIds = matches.map((m) => m.id);
  const { data: predictions } = await supabase
    .from("match_predictions")
    .select("*")
    .in("match_id", matchIds);

  const predMap = new Map((predictions ?? []).map((p) => [p.match_id, p]));

  return matches.map((m) => ({
    ...m,
    prediction: predMap.get(m.id) ?? null,
  }));
}

async function Page() {
  const matches = await getUpcomingMatches();

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-2 tracking-tight text-slate-800">
        Match Predictions
      </h1>
      <p className="text-slate-500 mb-8">
        Proximos partidos de la Premier League con predicciones impulsadas por IA
      </p>

      {matches.length === 0 ? (
        <p className="text-slate-400 text-center py-12">
          No hay partidos programados.
        </p>
      ) : (
        <div className="space-y-4">
          {matches.map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      )}
    </main>
  );
}

export default Page;
