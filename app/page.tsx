import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-16">
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold mb-4 tracking-tight">
          <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Furbocore
          </span>{" "}
          Analytics
        </h1>
        <p className="text-lg text-slate-500">
          Premier League data-driven insights
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <Link
          href="/transfers"
          className="group block rounded-2xl p-6 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 card-gradient-blue"
        >
          <div className="text-3xl mb-3">&#8364;</div>
          <h2 className="text-xl font-semibold mb-2">Transfer Values</h2>
          <p className="text-blue-100 text-sm">
            Player valuations, predicted market value, and over/under-rating analysis.
          </p>
        </Link>

        <Link
          href="/matches"
          className="group block rounded-2xl p-6 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 card-gradient-green"
        >
          <div className="text-3xl mb-3">&#9917;</div>
          <h2 className="text-xl font-semibold mb-2">Match Predictions</h2>
          <p className="text-green-100 text-sm">
            Upcoming fixtures with AI-powered win/draw/loss probabilities.
          </p>
        </Link>

        <Link
          href="/scouting"
          className="group block rounded-2xl p-6 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 card-gradient-purple"
        >
          <div className="text-3xl mb-3">&#128269;</div>
          <h2 className="text-xl font-semibold mb-2">Scouting</h2>
          <p className="text-purple-100 text-sm">
            Find similar players using clustering and vector similarity search.
          </p>
        </Link>
      </div>
    </main>
  );
}
