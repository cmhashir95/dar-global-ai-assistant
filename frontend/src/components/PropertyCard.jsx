export default function PropertyCard({ property, onAsk }) {
  const bedrooms = property.bedrooms.join("/");
  return (
    <div className="blueprint-corners bg-white border border-ink/10 p-6 flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-mono text-[11px] tracking-wider text-brass">{property.id}</p>
          <h3 className="font-display text-2xl mt-1">{property.name}</h3>
          <p className="text-sm text-muted mt-1">
            {property.community}, {property.city}, {property.country}
          </p>
        </div>
        <span className="text-[11px] font-mono uppercase tracking-wide border border-ink/15 px-2 py-1 text-ink/70 whitespace-nowrap">
          {property.status}
        </span>
      </div>

      <p className="text-sm text-ink/80 leading-relaxed">{property.highlights}</p>

      <dl className="grid grid-cols-2 gap-y-2 text-sm border-t border-ink/10 pt-4 font-mono">
        <dt className="text-muted">Bedrooms</dt>
        <dd>{bedrooms}</dd>
        <dt className="text-muted">From</dt>
        <dd>${property.price_from_usd.toLocaleString()}</dd>
        <dt className="text-muted">Size</dt>
        <dd>{property.size_sqft[0]}–{property.size_sqft[1]} sqft</dd>
        <dt className="text-muted">Handover</dt>
        <dd>{property.handover}</dd>
      </dl>

      <button
        onClick={() => onAsk(property)}
        className="mt-2 text-sm font-semibold text-brass hover:text-ink transition-colors text-left"
      >
        Ask the assistant about this property →
      </button>
    </div>
  );
}
