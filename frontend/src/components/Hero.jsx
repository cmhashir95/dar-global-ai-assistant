export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-ink text-parchment">
      {/* Blueprint grid: thin hairlines + coordinate ticks, evoking a site
          plan drawing -- the recurring device carried through the property
          cards and chat panel below. */}
      <svg
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.14]"
        viewBox="0 0 1200 700"
        preserveAspectRatio="none"
      >
        {Array.from({ length: 25 }).map((_, i) => (
          <line key={`v${i}`} x1={i * 50} y1="0" x2={i * 50} y2="700" stroke="#C7A876" strokeWidth="0.5" />
        ))}
        {Array.from({ length: 15 }).map((_, i) => (
          <line key={`h${i}`} x1="0" y1={i * 50} x2="1200" y2={i * 50} stroke="#C7A876" strokeWidth="0.5" />
        ))}
      </svg>

      <div className="relative mx-auto max-w-6xl px-6 pt-24 pb-28">
        <p className="font-mono text-xs tracking-[0.25em] text-brass-light uppercase mb-6">
          Dubai — Riyadh — London — Marbella
        </p>
        <h1 className="font-display text-5xl sm:text-6xl leading-[1.05] max-w-2xl">
          Branded residences, drawn to a{" "}
          <span className="italic text-brass-light">different standard.</span>
        </h1>
        <p className="mt-6 max-w-lg text-parchment/70 text-lg leading-relaxed">
          Explore Dar Global's current developments, or ask our AI property assistant for exact
          pricing, floor sizes, and availability -- then book a call with the consultant best
          suited to what you're looking for.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <a href="#developments" className="bg-brass-light text-ink px-6 py-3 text-sm font-semibold hover:bg-parchment transition-colors">
            View developments
          </a>
          <a href="#assistant" className="border border-parchment/30 px-6 py-3 text-sm font-semibold hover:border-brass-light hover:text-brass-light transition-colors">
            Chat with the assistant
          </a>
        </div>
      </div>
    </section>
  );
}
