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
        .limit(10);
      setResults(data ?? []);
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
        placeholder="Search player name (min 2 chars)..."
        className="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        onChange={(e) => {
          const v = e.target.value;
          setQuery(v);
          fetchPlayers(v);
        }}
      />
      {isPending && (
        <div className="absolute right-3 top-3.5 text-gray-400 animate-pulse">...</div>
      )}
      {open && results.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-72 overflow-y-auto">
          {results.map((p) => (
            <li
              key={p.id}
              onClick={() => handleSelect(p.id)}
              className="px-4 py-3 cursor-pointer hover:bg-blue-50 flex justify-between items-center"
            >
              <div>
                <div className="font-medium">{p.name}</div>
                <div className="text-sm text-gray-500">{p.team}</div>
              </div>
              <span className="text-xs bg-gray-100 px-2 py-1 rounded">{p.position}</span>
            </li>
          ))}
        </ul>
      )}
      {open && query.length >= 2 && results.length === 0 && !isPending && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-gray-500 text-center">
          No players found
        </div>
      )}
    </div>
  );
}
