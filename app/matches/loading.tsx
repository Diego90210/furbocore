export default function Loading() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-slate-200 rounded-lg w-56" />
        <div className="h-4 bg-slate-200 rounded-lg w-80" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-2xl" />
          ))}
        </div>
      </div>
    </main>
  );
}
