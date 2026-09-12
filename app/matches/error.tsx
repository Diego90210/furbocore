"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto max-w-5xl px-4 py-16 text-center">
      <h2 className="text-xl font-semibold mb-2 text-slate-800">Algo salio mal</h2>
      <p className="text-slate-500 mb-4">{error.message}</p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Intentar de nuevo
      </button>
    </main>
  );
}
