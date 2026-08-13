export default function Footer() {
  return (
    <footer id="about" className="bg-ink text-parchment/60 py-12">
      <div className="mx-auto max-w-6xl px-6 flex flex-col sm:flex-row justify-between gap-4 text-xs">
        <p>
          Demo portfolio project. Property data is synthetic and does not represent real Dar Global
          listings, pricing, or availability.
        </p>
        <p className="font-mono">dar-global-ai-assistant · MIT licensed</p>
      </div>
    </footer>
  );
}
