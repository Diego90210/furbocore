import { Suspense } from "react";
import { supabase } from "@/lib/supabase";
import PlayerSearchBox from "@/components/PlayerSearchBox";
import PlayerCard from "./PlayerCard";

export const revalidate = 86400;

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

  let stats: any[] = [];
  let value = null;

  if (playerId) {
    const data = await getPlayerData(playerId);
    stats = data.stats;
    value = data.value;
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-2 tracking-tight text-slate-800">
        Transfer Value Analyzer
      </h1>
      <p className="text-slate-500 mb-8">
        Valores de mercado, prediccion y analisis de rating
      </p>

      <PlayerSearchBox module="transfers" initialQuery={query} />

      {playerId ? (
        <Suspense fallback={<div className="mt-6 text-slate-400">Cargando datos del jugador...</div>}>
          <PlayerCard stats={stats} value={value} />
        </Suspense>
      ) : (
        <p className="mt-12 text-slate-400 text-center">
          Busca un jugador para ver sus estadisticas y valor de mercado.
        </p>
      )}
    </main>
  );
}

export default Page;
