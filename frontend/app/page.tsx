export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-4">uBackend Studio</h1>
      <p className="text-gray-500">Low-Code Platform Core</p>
      <div className="mt-8 p-4 border rounded bg-gray-100">
        Status: <span className="text-green-600 font-bold">Connecting...</span>
      </div>
    </main>
  );
}
