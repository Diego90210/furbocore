"use client";

interface Player {
  id: string;
  name: string;
  team: string;
  position: string;
}

interface SimilarPlayer extends Player {
  similarity: number;
}

const FEATURE_LABELS: Record<string, string> = {
  goals_per90: "Goles",
  assists_per90: "Asistencias",
};

function RadarChart({ features }: { features: Record<string, number> }) {
  const keys = Object.keys(features);
  const n = keys.length;
  const size = 200;
  const center = size / 2;
  const radius = 80;

  const normalize = (v: number) => Math.min(100, Math.max(0, (v + 3) * (100 / 6)));
  const angleStep = (2 * Math.PI) / n;

  const getPoint = (i: number, value: number) => {
    const angle = i * angleStep - Math.PI / 2;
    const r = (value / 100) * radius;
    return { x: center + r * Math.cos(angle), y: center + r * Math.sin(angle) };
  };

  const gridLevels = [20, 40, 60, 80, 100];

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {gridLevels.map((level) => (
        <polygon
          key={level}
          points={keys.map((_, i) => {
            const p = getPoint(i, level);
            return `${p.x},${p.y}`;
          }).join(" ")}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="1"
        />
      ))}
      {keys.map((_, i) => {
        const p = getPoint(i, 100);
        return <line key={i} x1={center} y1={center} x2={p.x} y2={p.y} stroke="#cbd5e1" strokeWidth="1" />;
      })}
      <polygon
        points={keys.map((k, i) => {
          const p = getPoint(i, normalize(features[k] ?? 0));
          return `${p.x},${p.y}`;
        }).join(" ")}
        fill="rgba(139, 92, 246, 0.15)"
        stroke="#8b5cf6"
        strokeWidth="2"
      />
      {keys.map((k, i) => {
        const p = getPoint(i, normalize(features[k] ?? 0));
        return <circle key={i} cx={p.x} cy={p.y} r="4" fill="#8b5cf6" />;
      })}
      {keys.map((k, i) => {
        const p = getPoint(i, 125);
        return (
          <text
            key={i}
            x={p.x}
            y={p.y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-[10px] fill-slate-500 font-medium"
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
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-800">{player.name}</h2>
            <p className="text-slate-500 text-sm">
              {player.team} &middot; {player.position}
            </p>
          </div>
        </div>

        {normalizedFeatures && (
          <div className="flex justify-center">
            <RadarChart features={normalizedFeatures} />
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 overflow-hidden">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider p-6 pb-4">
          Jugadores Similares
        </h2>
        {similar.length === 0 ? (
          <p className="px-6 pb-4 text-slate-400">No se encontraron jugadores similares.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-t border-slate-100">
                <tr>
                  <th className="px-6 py-3 text-left font-semibold text-slate-500 text-xs uppercase tracking-wider">
                    Jugador
                  </th>
                  <th className="px-6 py-3 text-left font-semibold text-slate-500 text-xs uppercase tracking-wider">
                    Equipo
                  </th>
                  <th className="px-6 py-3 text-left font-semibold text-slate-500 text-xs uppercase tracking-wider">
                    Posicion
                  </th>
                  <th className="px-6 py-3 text-right font-semibold text-slate-500 text-xs uppercase tracking-wider">
                    Similitud
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {similar.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-3 font-semibold text-slate-700">{p.name}</td>
                    <td className="px-6 py-3 text-slate-500">{p.team}</td>
                    <td className="px-6 py-3 text-slate-500">{p.position}</td>
                    <td className="px-6 py-3 text-right">
                      <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
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
