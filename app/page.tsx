import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-16">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Furbocore Analytics</h1>
        <p className="text-lg text-gray-600">
          Premier League data-driven insights
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <Link
          href="/transfers"
          className="block bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
        >
          <h2 className="text-xl font-semibold mb-2">Transfer Values</h2>
          <p className="text-gray-500 text-sm">
            Player valuations, predicted market value, and over/under-rating analysis.
          </p>
        </Link>

        <Link
          href="/matches"
          className="block bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
        >
          <h2 className="text-xl font-semibold mb-2">Match Predictions</h2>
          <p className="text-gray-500 text-sm">
            Upcoming fixtures with AI-powered win/draw/loss probabilities.
          </p>
        </Link>

        <Link
          href="/scouting"
          className="block bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
        >
          <h2 className="text-xl font-semibold mb-2">Scouting</h2>
          <p className="text-gray-500 text-sm">
            Find similar players using clustering and vector similarity search.
          </p>
        </Link>
      </div>
    </main>
  );
}
