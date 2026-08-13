export default function Nav() {
  return (
    <header className="sticky top-0 z-40 bg-ink/95 backdrop-blur text-parchment">
      <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
        <div className="font-display text-lg tracking-wide">
          Dar<span className="text-brass-light"> Global</span>
        </div>
        <nav className="hidden sm:flex items-center gap-8 text-sm font-medium text-parchment/80">
          <a href="#developments" className="hover:text-brass-light transition-colors">Developments</a>
          <a href="#assistant" className="hover:text-brass-light transition-colors">Ask the assistant</a>
          <a href="#about" className="hover:text-brass-light transition-colors">About</a>
        </nav>
        <a
          href="#assistant"
          className="text-sm font-medium border border-brass-light/60 text-brass-light px-4 py-2 hover:bg-brass-light hover:text-ink transition-colors"
        >
          Talk to a consultant
        </a>
      </div>
    </header>
  );
}
