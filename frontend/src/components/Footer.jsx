import { Github, Mail } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-lg font-semibold text-slate-900">RMHT</p>
          <p className="text-sm text-slate-500">
            Turn real-time sentiment into actionable team rituals.
          </p>
        </div>
        <div className="flex items-center gap-4 text-slate-500">
          <a href="https://github.com/AgentTreeAi" className="transition hover:text-sky-600" target="_blank" rel="noreferrer">
            <Github className="h-5 w-5" />
          </a>
          <a href="mailto:team@rmht.app" className="transition hover:text-sky-600">
            <Mail className="h-5 w-5" />
          </a>
        </div>
      </div>
    </footer>
  );
}
