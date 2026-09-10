export default function Loading() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-44" />
        <div className="h-4 bg-gray-200 rounded w-72" />
        <div className="h-12 bg-gray-200 rounded" />
        <div className="bg-gray-200 rounded h-64" />
      </div>
    </main>
  );
}
