"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useTransition } from "react";

export default function PlayerSearch({ initialQuery }: { initialQuery: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const handleSearch = useCallback(
    (value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value.length >= 2) {
        params.set("q", value);
      } else {
        params.delete("q");
        params.delete("id");
      }
      startTransition(() => {
        router.push(`/transfers?${params.toString()}`);
      });
    },
    [router, searchParams, startTransition]
  );

  const handleSelect = useCallback(
    (id: string) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("id", id);
      startTransition(() => {
        router.push(`/transfers?${params.toString()}`);
      });
    },
    [router, searchParams, startTransition]
  );

  return (
    <div className="relative">
      <input
        type="text"
        defaultValue={initialQuery}
        placeholder="Search player name (min 2 chars)..."
        className="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        onChange={(e) => handleSearch(e.target.value)}
      />
      {isPending && (
        <div className="absolute right-3 top-3.5 text-gray-400 animate-pulse">...</div>
      )}
    </div>
  );
}
