import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-16 text-center">
      <h2 className="text-3xl font-bold mb-2 text-slate-800">404</h2>
      <p className="text-slate-500 mb-6">Pagina no encontrada</p>
      <Link
        href="/"
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Volver al inicio
      </Link>
    </main>
  );
}
