import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';
import { Activity, Users, TrendingUp } from 'lucide-react';
import { fetchDashboard } from '../lib/api';
import { Card } from '../components/Card';
import { RiskBadge } from '../components/RiskBadge';

const WEEK_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function formatSeries(series = []) {
  return WEEK_LABELS.map((label, index) => {
    const point = { name: label };
    series.forEach((entry) => {
      point[entry.name] = entry.data[index] ?? null;
    });
    return point;
  });
}

export function DashboardPage() {
  const { teamId = 'demo' } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    fetchDashboard(teamId)
      .then((response) => {
        if (mounted) {
          setData(response);
          setError(null);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || 'Unable to load dashboard');
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [teamId]);

  const chartData = formatSeries(data?.series || []);
  const summary = data?.summary || {};

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-4 py-16">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Team dashboard</h1>
            <p className="mt-2 text-sm text-slate-500">
              Weekly sentiment and participation snapshots for team <span className="font-semibold text-slate-700">{teamId}</span>.
            </p>
          </div>
          <RiskBadge level={summary.risk_level} />
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <Card title="Mood score" icon={TrendingUp} value={summary.sentiment ? `${summary.sentiment}%` : '--'}>
            <p className="text-sm text-slate-500">
              Collective morale from weekly pulses.
            </p>
          </Card>
          <Card title="Participation" icon={Users} value={summary.participation ? `${summary.participation}%` : '--'}>
            <p className="text-sm text-slate-500">Members who completed rituals in the last 7 days.</p>
          </Card>
          <Card title="Active rituals" icon={Activity} value={summary.active_rituals || '4'}>
            <p className="text-sm text-slate-500">Includes check-ins, async retros, and coaching prompts.</p>
          </Card>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Mood & stress over time</h2>
            <p className="text-xs text-slate-400">Last 7 days</p>
          </div>
          <div className="mt-6 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" domain={[0, 100]} />
                <Tooltip contentStyle={{ borderRadius: '1rem', borderColor: '#e2e8f0' }} />
                <Line type="monotone" dataKey="Mood" stroke="#0ea5e9" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="Stress" stroke="#f97316" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">Highlights</h3>
            <ul className="mt-4 space-y-3 text-sm text-slate-600">
              {(summary.highlights || ['Encourage async kudos ritual on Wednesday', 'Celebrate improvement in stress trends', 'Review upcoming OKR check-in flow']).map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <span className="mt-1 h-2 w-2 rounded-full bg-sky-400" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">Activity feed</h3>
            <div className="mt-4 space-y-4 text-sm text-slate-600">
              <p>✅ Weekly async retro completed by 92% of the team.</p>
              <p>🤖 Coaching prompt delivered to EMs with tailored follow-ups.</p>
              <p>🧠 Wellness workshop reminder scheduled via Slack integration.</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-sm text-slate-500">Loading latest metrics…</div>
        )}
      </div>
    </div>
  );
}
