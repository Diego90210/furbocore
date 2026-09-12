import { supabase } from "@/lib/supabase";
import PlayerSearchBox from "@/components/PlayerSearchBox";
import SimilarPlayers from "./SimilarPlayers";

export const revalidate = 86400;

async function getSimilarPlayers(playerId: string) {
  const { data: cluster } = await supabase
    .from("player_clusters")
    .select("position_group, feature_vector, normalized_features")
    .eq("player_id", playerId)
    .order("season", { ascending: false })
    .limit(1)
    .single();

  if (!cluster) return { player: null, similar: [], normalizedFeatures: null };

  const { data: player } = await supabase
    .from("players")
    .select("id, name, team, position")
    .eq("id", playerId)
    .single();

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

  let similarData = { player: null as any, similar: [] as any[], normalizedFeatures: null as any };
  if (playerId) {
    similarData = await getSimilarPlayers(playerId);
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-2 tracking-tight text-slate-800">
        Scouting Tool
      </h1>
      <p className="text-slate-500 mb-8">
        Busca jugadores similares usando clustering y busqueda por similitud vectorial
      </p>

      <PlayerSearchBox module="scouting" initialQuery={query} />

      {playerId && similarData.player ? (
        <SimilarPlayers
          player={similarData.player}
          similar={similarData.similar}
          normalizedFeatures={similarData.normalizedFeatures}
        />
      ) : (
        <p className="mt-12 text-slate-400 text-center">
          Busca un jugador para encontrar perfiles similares.
        </p>
      )}
    </main>
  );
}

export default Page;
