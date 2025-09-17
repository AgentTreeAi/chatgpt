import { useState } from 'react';
import { sendSlackTest, goToBilling, requestSlackInstall } from '../lib/api';
import { Card } from '../components/Card';
import { Bot, MessageCircle, CreditCard, Slack } from 'lucide-react';

export function AdminPage() {
  const [channel, setChannel] = useState('team-rituals');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleTest = async () => {
    try {
      setLoading(true);
      setStatus(null);
      const response = await sendSlackTest(channel);
      const message = typeof response === 'string' ? response : response?.detail || 'Test message sent!';
      setStatus({ type: 'success', message });
    } catch (error) {
      setStatus({ type: 'error', message: error.message || 'Failed to send test.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-4xl flex-col gap-10 px-4 py-16">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">Admin console</h1>
          <p className="mt-2 text-sm text-slate-500">Configure integrations and manage billing for your rituals hub.</p>
        </div>

        <div className="space-y-6">
          <Card
            title="Connect Slack"
            icon={Slack}
            description="Install the RMHT Slack app to deliver nudges and capture quick reactions."
          >
            <button
              type="button"
              onClick={requestSlackInstall}
              className="mt-4 inline-flex items-center gap-2 rounded-full bg-sky-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-700"
            >
              <Bot className="h-4 w-4" /> Install Slack
            </button>
          </Card>

          <Card
            title="Send a test message"
            icon={MessageCircle}
            description="Verify RMHT can post to your ritual channel."
          >
            <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center">
              <input
                type="text"
                value={channel}
                onChange={(event) => setChannel(event.target.value)}
                className="w-full rounded-full border border-slate-200 px-4 py-2 text-sm shadow-inner focus:border-sky-300 focus:outline-none focus:ring-2 focus:ring-sky-200"
                placeholder="#channel or user"
              />
              <button
                type="button"
                onClick={handleTest}
                disabled={loading}
                className="inline-flex items-center justify-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {loading ? 'Sending…' : 'Send test'}
              </button>
            </div>
            {status && (
              <div
                className={`mt-3 rounded-full px-4 py-2 text-xs font-medium ${
                  status.type === 'success'
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-rose-100 text-rose-700'
                }`}
              >
                {status.message}
              </div>
            )}
          </Card>

          <Card
            title="Billing"
            icon={CreditCard}
            description="Upgrade to unlock proactive coach nudges, deep insights, and enterprise rituals."
          >
            <button
              type="button"
              onClick={() => goToBilling('starter')}
              className="mt-4 inline-flex items-center justify-center rounded-full border border-sky-200 px-5 py-2 text-sm font-semibold text-sky-600 transition hover:bg-sky-50"
            >
              Subscribe (Test)
            </button>
          </Card>
        </div>
      </div>
    </div>
  );
}
