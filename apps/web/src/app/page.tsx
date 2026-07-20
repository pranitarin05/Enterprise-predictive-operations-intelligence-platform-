"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [status, setStatus] = useState<string>("checking...");

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((res) => res.json())
      .then((data) => setStatus(JSON.stringify(data)))
      .catch((err) => setStatus(`Error: ${err.message}`));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-24">
      <h1 className="text-3xl font-bold">EPOIP</h1>
      <p className="text-gray-500">Enterprise Predictive Operations Intelligence Platform</p>
      <div className="mt-8 rounded border p-4 font-mono text-sm">
        Backend health check: {status}
      </div>
    </main>
  );
}
