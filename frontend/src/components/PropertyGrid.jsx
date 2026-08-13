import { useEffect, useState } from "react";
import { getProperties } from "../lib/api";
import PropertyCard from "./PropertyCard";

export default function PropertyGrid({ onAskAbout }) {
  const [properties, setProperties] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getProperties()
      .then(setProperties)
      .catch(() => setError("Couldn't reach the backend. Is the API server running?"));
  }, []);

  return (
    <section id="developments" className="mx-auto max-w-6xl px-6 py-24">
      <div className="flex items-end justify-between mb-10 border-b border-ink/10 pb-6">
        <div>
          <p className="font-mono text-xs tracking-[0.25em] text-brass uppercase mb-2">Current developments</p>
          <h2 className="font-display text-4xl">Where we're building</h2>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-700 bg-red-50 border border-red-200 px-4 py-3 mb-8">
          {error} Start it with <code className="font-mono">uvicorn app.main:app --reload</code> from{" "}
          <code className="font-mono">backend/</code>.
        </p>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {properties.map((p) => (
          <PropertyCard key={p.id} property={p} onAsk={onAskAbout} />
        ))}
      </div>
    </section>
  );
}
