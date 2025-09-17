import { motion } from 'framer-motion';
import { CalendarCheck, Sparkles, BarChart3, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

const features = [
  {
    title: 'Pulse-driven rituals',
    description: 'Launch weekly check-ins, retro nudges, and follow-ups with AI-crafted agendas.',
    icon: CalendarCheck,
  },
  {
    title: 'Insights you can act on',
    description: 'Understand sentiment, workload, and participation trends in one streamlined hub.',
    icon: BarChart3,
  },
  {
    title: 'Automations that delight',
    description: 'Let RMHT sync updates to Slack and your tools while you focus on coaching moments.',
    icon: Sparkles,
  },
  {
    title: 'Privacy-first approach',
    description: 'Aggregated analytics and fine-grained controls to keep every ritual psychologically safe.',
    icon: ShieldCheck,
  },
];

export function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-20 px-4 py-16">
        <section className="grid gap-12 lg:grid-cols-[1.1fr,0.9fr] lg:items-center">
          <div className="space-y-6">
            <motion.span
              className="inline-flex rounded-full bg-sky-50 px-4 py-1 text-sm font-medium text-sky-600"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              Rituals that keep teams healthy & high-performing
            </motion.span>
            <motion.h1
              className="text-4xl font-bold tracking-tight text-slate-900 md:text-5xl"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              Transform raw sentiment into rituals your team actually loves.
            </motion.h1>
            <motion.p
              className="text-lg text-slate-600 md:text-xl"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              RMHT helps you observe mood, stress, and participation trends in real time—and then nudges the right
              rituals to keep everyone aligned, supported, and energized.
            </motion.p>
            <motion.div
              className="flex flex-col gap-3 sm:flex-row"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <a
                href="#features"
                className="inline-flex items-center justify-center rounded-full bg-sky-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-sky-200 transition hover:bg-sky-700"
              >
                Explore the platform
              </a>
              <Link
                to="/dashboard/demo"
                className="inline-flex items-center justify-center rounded-full border border-slate-200 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:border-sky-200 hover:text-sky-600"
              >
                See the dashboard
              </Link>
            </motion.div>
          </div>
          <motion.div
            className="relative"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
          >
            <div className="absolute inset-0 rounded-3xl bg-gradient-to-tr from-sky-100 via-transparent to-transparent blur-xl" />
            <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl shadow-sky-100">
              <img src="https://images.unsplash.com/photo-1529333166437-7750a6dd5a70?auto=format&fit=crop&w=900&q=80" alt="Team collaboration" className="h-full w-full object-cover" />
            </div>
          </motion.div>
        </section>

        <section id="features" className="space-y-12">
          <div className="text-center">
            <h2 className="text-3xl font-semibold text-slate-900">A ritual platform for modern teams</h2>
            <p className="mt-3 text-base text-slate-500">
              Every workflow surfaces the right signal at the right moment, so you can lead with clarity and care.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
              >
                <div className="flex items-center gap-3">
                  <feature.icon className="h-10 w-10 rounded-full bg-sky-50 p-2 text-sky-600" />
                  <h3 className="text-lg font-semibold text-slate-900">{feature.title}</h3>
                </div>
                <p className="mt-4 text-sm text-slate-500">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
