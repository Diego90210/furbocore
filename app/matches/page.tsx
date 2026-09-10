import { supabase } from "@/lib/supabase";
import MatchCard from "./MatchCard";

export const revalidate = 3600; // 1h

async function getUpcomingMatches() {
  const { data: matches } = await supabase
    .from("matches")
    .select("*")
    .eq("status", "scheduled")
    .order("match_date", { ascending: true })
    .limit(10);

  if (!matches || matches.length === 0) return [];

  // Fetch predictions for these matches
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

async function getH2H(homeTeam: string, awayTeam: string) {
  const { data } = await supabase
    .from("matches")
    .select("match_date, home_team, away_team, home_goals, away_goals")
    .eq("status", "played")
    .or(`and(home_team.eq.${homeTeam},away_team.eq.${awayTeam}),and(home_team.eq.${awayTeam},away_team.eq.${homeTeam})`)
    .order("match_date", { ascending: false })
    .limit(5);

  return data ?? [];
}

async function Page() {
  const matches = await getUpcomingMatches();

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">Match Predictions</h1>
      <p className="text-gray-500 mb-8">Upcoming Premier League fixtures with AI-powered predictions</p>

      {matches.length === 0 ? (
        <p className="text-gray-500 text-center py-12">No upcoming matches scheduled.</p>
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
