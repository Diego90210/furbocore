import { Suspense } from "react";
import { supabase } from "@/lib/supabase";
import PlayerSearch from "./PlayerSearch";
import PlayerCard from "./PlayerCard";

export const revalidate = 86400; // 24h

async function searchPlayers(query: string) {
  if (!query || query.length < 2) return [];
  const { data } = await supabase
    .from("players")
    .select("id, name, team, position")
    .ilike("name", `%${query}%`)
    .order("name")
    .limit(10);
  return data ?? [];
}

async function getPlayerData(playerId: string) {
  const [statsRes, valueRes] = await Promise.all([
    supabase
      .from("player_stats")
      .select("*")
      .eq("player_id", playerId)
      .order("season", { ascending: true }),
    supabase
      .from("transfer_values")
      .select("real_value_eur, predicted_value_eur, value_gap_pct")
      .eq("player_id", playerId)
      .single(),
  ]);
  return { stats: statsRes.data ?? [], value: valueRes.data };
}

async function Page({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; id?: string }>;
}) {
  const params = await searchParams;
  const query = params.q ?? "";
  const playerId = params.id ?? "";

  let player = null;
  let stats: any[] = [];
  let value = null;

  if (playerId) {
    const data = await getPlayerData(playerId);
    stats = data.stats;
    value = data.value;
    if (stats.length > 0) {
      player = { id: playerId };
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Transfer Value Analyzer</h1>

      <PlayerSearch initialQuery={query} />

      {playerId && (
        <Suspense fallback={<div className="mt-6 text-gray-500">Loading player data...</div>}>
          <PlayerCard stats={stats} value={value} />
        </Suspense>
      )}

      {!playerId && (
        <p className="mt-8 text-gray-500 text-center">
          Search for a player to see their stats and transfer valuation.
        </p>
      )}
    </main>
  );
}

export default Page;
