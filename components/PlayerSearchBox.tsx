"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import { supabase } from "@/lib/supabase";

interface Player {
  id: string;
  name: string;
  team: string;
  position: string;
}

const POS_COLOR: Record<string, string> = {
  GK: "bg-amber-100 text-amber-700",
  DF: "bg-blue-100 text-blue-700",
  MF: "bg-emerald-100 text-emerald-700",
  FW: "bg-rose-100 text-rose-700",
};

export default function PlayerSearchBox({
  module,
  initialQuery,
}: {
  module: "transfers" | "scouting";
  initialQuery: string;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<Player[]>([]);
  const [open, setOpen] = useState(false);
  const [isPending, startTransition] = useTransition();
  const timer = useRef<ReturnType<typeof setTimeout>>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchPlayers = useCallback((value: string) => {
    if (timer.current) clearTimeout(timer.current);
    if (value.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }
    timer.current = setTimeout(async () => {
      const { data } = await supabase
        .from("players")
        .select("id, name, team, position")
        .ilike("name", `%${value}%`)
        .order("name")
        .limit(20);
      const seen = new Set<string>();
      const unique = (data ?? [])
        .filter((p) => {
          if (seen.has(p.name)) return false;
          seen.add(p.name);
          return true;
        })
        .slice(0, 10);
      setResults(unique);
      setOpen(true);
    }, 200);
  }, []);

  const handleSelect = useCallback(
    (id: string) => {
      setOpen(false);
      setQuery("");
      const params = new URLSearchParams(searchParams.toString());
      params.set("id", id);
      params.delete("q");
      startTransition(() => {
        router.push(`/${module}?${params.toString()}`);
      });
    },
    [router, searchParams, startTransition, module]
  );

  return (
    <div ref={wrapperRef} className="relative">
      <input
        type="text"
        value={query}
        placeholder="Buscar jugador (min. 2 caracteres)..."
        className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-lg focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400 shadow-sm transition-all"
        onChange={(e) => {
          const v = e.target.value;
          setQuery(v);
          fetchPlayers(v);
        }}
      />
      {isPending && (
        <div className="absolute right-3 top-3.5 text-slate-400 animate-pulse">...</div>
      )}
      {open && results.length > 0 && (
        <ul className="absolute z-10 mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-xl max-h-72 overflow-y-auto">
          {results.map((p) => (
            <li
              key={p.id}
              onClick={() => handleSelect(p.id)}
              className="px-4 py-3 cursor-pointer hover:bg-slate-50 flex justify-between items-center transition-colors first:rounded-t-xl last:rounded-b-xl"
            >
              <div>
                <div className="font-semibold text-slate-800">{p.name}</div>
                <div className="text-sm text-slate-400">{p.team}</div>
              </div>
              <span
                className={`text-xs px-2 py-0.5 rounded-md font-medium ${
                  POS_COLOR[p.position] ?? "bg-slate-100 text-slate-600"
                }`}
              >
                {p.position}
              </span>
            </li>
          ))}
        </ul>
      )}
      {open && query.length >= 2 && results.length === 0 && !isPending && (
        <div className="absolute z-10 mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-xl p-4 text-slate-400 text-center">
          No se encontraron jugadores
        </div>
      )}
    </div>
  );
}
