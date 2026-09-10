import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-16 text-center">
      <h2 className="text-3xl font-bold mb-2">404</h2>
      <p className="text-gray-500 mb-6">Page not found</p>
      <Link
        href="/"
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Go home
      </Link>
    </main>
  );
}
