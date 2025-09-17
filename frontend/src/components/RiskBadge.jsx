const COLORS = {
  low: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-rose-100 text-rose-700',
};

export function RiskBadge({ level = 'low' }) {
  const normalized = (level || 'low').toLowerCase();
  const classes = COLORS[normalized] || COLORS.low;
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${classes}`}>
      {normalized} risk
    </span>
  );
}
