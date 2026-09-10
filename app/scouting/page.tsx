import { supabase } from "@/lib/supabase";
import SimilarPlayers from "./SimilarPlayers";
import SearchPlayer from "./SearchPlayer";

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

async function getSimilarPlayers(playerId: string) {
  // Get player's position_group and feature_vector
  const { data: cluster } = await supabase
    .from("player_clusters")
    .select("position_group, feature_vector, normalized_features")
    .eq("player_id", playerId)
    .order("season", { ascending: false })
    .limit(1)
    .single();

  if (!cluster) return { player: null, similar: [], normalizedFeatures: null };

  // Get player info
  const { data: player } = await supabase
    .from("players")
    .select("id, name, team, position")
    .eq("id", playerId)
    .single();

  // Query similar players using pgvector
  // feature_vector is the scaled vector — use L2 distance
  const { data: similar } = await supabase.rpc("similar_players", {
    query_vector: cluster.feature_vector,
    pos_group: cluster.position_group,
    exclude_id: playerId,
    match_count: 10,
  });

  return {
    player,
    similar: similar ?? [],
    normalizedFeatures: cluster.normalized_features,
  };
}

async function Page({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; id?: string }>;
}) {
  const params = await searchParams;
  const query = params.q ?? "";
  const playerId = params.id ?? "";

  let similarData: { player: any; similar: any[]; normalizedFeatures: any } = {
    player: null,
    similar: [],
    normalizedFeatures: null,
  };
  if (playerId) {
    similarData = await getSimilarPlayers(playerId);
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">Scouting Tool</h1>
      <p className="text-gray-500 mb-8">
        Find similar players using AI-powered clustering and vector similarity
      </p>

      <SearchPlayer initialQuery={query} />

      {playerId && similarData.player ? (
        <SimilarPlayers
          player={similarData.player}
          similar={similarData.similar}
          normalizedFeatures={similarData.normalizedFeatures}
        />
      ) : (
        <p className="mt-8 text-gray-500 text-center">
          Search for a player to find similar profiles.
        </p>
      )}
    </main>
  );
}

export default Page;
