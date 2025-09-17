import { useState } from 'react';
import { requestDevLogin } from '../lib/api';
import { Sparkle } from 'lucide-react';

export function DevLoginPage() {
  const [email, setEmail] = useState('demo@example.com');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setLoading(true);
      setResult(null);
      const response = await requestDevLogin(email);
      setResult({
        type: 'success',
        link: response?.login_url,
        message: response?.detail || 'Magic link ready. Open the URL to continue.',
      });
    } catch (error) {
      setResult({ type: 'error', message: error.message || 'Failed to request link.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="mx-auto flex max-w-lg flex-col gap-10 px-4 py-16">
        <div className="space-y-3 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-sky-500/20">
            <Sparkle className="h-7 w-7 text-sky-300" />
          </div>
          <h1 className="text-3xl font-semibold">Developer login</h1>
          <p className="text-sm text-slate-300">
            Request a local magic link for testing flows without sending real emails. Use the seeded
            <span className="font-semibold text-sky-200"> demo@example.com</span> account to explore admin pages.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-3xl border border-white/10 bg-white/5 p-8 shadow-xl backdrop-blur">
          <div className="space-y-2 text-left">
            <label htmlFor="email" className="text-sm font-medium text-slate-200">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm text-white placeholder:text-slate-400 focus:border-sky-300 focus:outline-none focus:ring-2 focus:ring-sky-400/40"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-sky-500 px-5 py-2 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-500"
          >
            {loading ? 'Generating link…' : 'Request magic link'}
          </button>
        </form>

        {result && (
          <div
            className={`rounded-3xl border px-6 py-4 text-sm ${
              result.type === 'success'
                ? 'border-emerald-400/50 bg-emerald-500/10 text-emerald-100'
                : 'border-rose-400/50 bg-rose-500/10 text-rose-100'
            }`}
          >
            <p className="font-medium">{result.message}</p>
            {result.link && (
              <a
                href={result.link}
                className="mt-3 inline-flex items-center text-sm font-semibold text-sky-200 underline"
              >
                Open login URL
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
