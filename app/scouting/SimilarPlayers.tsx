"use client";

interface Player {
  id: string;
  name: string;
  team: string;
  position: string;
}

interface SimilarPlayer extends Player {
  similarity: number;
  cluster_id?: number;
  normalized_features?: Record<string, number>;
}

const FEATURE_LABELS: Record<string, string> = {
  goals_per90: "Goals",
  assists_per90: "Assists",
  shots_per90: "Shots",
  tackles_per90: "Tackles",
  interceptions_per90: "Interceptions",
};

function RadarChart({ features }: { features: Record<string, number> }) {
  const keys = Object.keys(features);
  const n = keys.length;
  const size = 200;
  const center = size / 2;
  const radius = 80;

  // Convert normalized features (z-scores) to 0-100 scale
  const normalize = (v: number) => Math.min(100, Math.max(0, (v + 3) * (100 / 6)));

  const angleStep = (2 * Math.PI) / n;

  const getPoint = (i: number, value: number) => {
    const angle = i * angleStep - Math.PI / 2;
    const r = (value / 100) * radius;
    return { x: center + r * Math.cos(angle), y: center + r * Math.sin(angle) };
  };

  // Grid circles
  const gridLevels = [20, 40, 60, 80, 100];

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Grid */}
      {gridLevels.map((level) => (
        <polygon
          key={level}
          points={keys.map((_, i) => {
            const p = getPoint(i, level);
            return `${p.x},${p.y}`;
          }).join(" ")}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="1"
        />
      ))}

      {/* Axes */}
      {keys.map((_, i) => {
        const p = getPoint(i, 100);
        return <line key={i} x1={center} y1={center} x2={p.x} y2={p.y} stroke="#d1d5db" strokeWidth="1" />;
      })}

      {/* Data polygon */}
      <polygon
        points={keys.map((k, i) => {
          const p = getPoint(i, normalize(features[k] ?? 0));
          return `${p.x},${p.y}`;
        }).join(" ")}
        fill="rgba(59, 130, 246, 0.2)"
        stroke="#3b82f6"
        strokeWidth="2"
      />

      {/* Data points */}
      {keys.map((k, i) => {
        const p = getPoint(i, normalize(features[k] ?? 0));
        return <circle key={i} cx={p.x} cy={p.y} r="3" fill="#3b82f6" />;
      })}

      {/* Labels */}
      {keys.map((k, i) => {
        const p = getPoint(i, 115);
        return (
          <text
            key={i}
            x={p.x}
            y={p.y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-[9px] fill-gray-600"
          >
            {FEATURE_LABELS[k] ?? k}
          </text>
        );
      })}
    </svg>
  );
}

export default function SimilarPlayers({
  player,
  similar,
  normalizedFeatures,
}: {
  player: Player;
  similar: SimilarPlayer[];
  normalizedFeatures: Record<string, number> | null;
}) {
  return (
    <div className="mt-6 space-y-6">
      {/* Base player */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold">{player.name}</h2>
            <p className="text-gray-500">
              {player.team} · {player.position}
            </p>
          </div>
        </div>

        {normalizedFeatures && (
          <div className="flex justify-center">
            <RadarChart features={normalizedFeatures} />
          </div>
        )}
      </div>

      {/* Similar players */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <h2 className="text-xl font-semibold p-6 pb-4">Similar Players</h2>
        {similar.length === 0 ? (
          <p className="px-6 pb-4 text-gray-500">No similar players found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-t">
                <tr>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Player</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Team</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Position</th>
                  <th className="px-6 py-3 text-right font-medium text-gray-500">Similarity</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {similar.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-6 py-3 font-medium">{p.name}</td>
                    <td className="px-6 py-3 text-gray-600">{p.team}</td>
                    <td className="px-6 py-3 text-gray-600">{p.position}</td>
                    <td className="px-6 py-3 text-right">
                      <span className="inline-block px-2 py-0.5 rounded text-sm font-medium bg-blue-50 text-blue-700">
                        {((p.similarity ?? 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
