export default function Loading() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-slate-200 rounded-lg w-48" />
        <div className="h-4 bg-slate-200 rounded-lg w-96" />
        <div className="h-12 bg-slate-200 rounded-xl" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-slate-200 rounded-2xl" />
          ))}
        </div>
      </div>
    </main>
  );
}
