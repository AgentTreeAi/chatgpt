export function Card({ title, icon: Icon, value, description, children }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sky-50 text-sky-600">
            <Icon className="h-5 w-5" />
          </div>
        )}
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          {value && <p className="text-2xl font-semibold text-slate-900">{value}</p>}
        </div>
      </div>
      {description && <p className="mt-4 text-sm text-slate-500">{description}</p>}
      {children && <div className="mt-4 text-sm text-slate-600">{children}</div>}
    </div>
  );
}
