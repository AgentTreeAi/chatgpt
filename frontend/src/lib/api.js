const API_BASE =
  (typeof window !== 'undefined' && window.__RMHT_BASE_URL__) ||
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_RMHT_API_BASE) ||
  "";

function getCsrfToken() {
  if (typeof document === 'undefined') return null;
  const raw = document.cookie
    ?.split('; ')
    .find((entry) => entry.startsWith('csrftoken='));
  if (!raw) return null;
  return decodeURIComponent(raw.split('=')[1]);
}

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const csrf = getCsrfToken();
  if (csrf && !headers['X-CSRF-Token'] && !headers['X-CSRF-TOKEN']) {
    headers['X-CSRF-Token'] = csrf;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers,
    ...options,
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (err) {
    data = text;
  }
  if (!res.ok) {
    const message = (data && data.detail) || res.statusText || 'Request failed';
    throw new Error(message);
  }
  return data;
}

export async function fetchDashboard(teamId) {
  try {
    return await apiFetch(`/api/dashboard/${teamId}`);
  } catch (error) {
    console.warn('Falling back to sample dashboard data:', error);
    return {
      series: [
        { name: 'Mood', data: [72, 68, 74, 70, 75, 77, 80] },
        { name: 'Stress', data: [45, 50, 48, 52, 49, 47, 44] },
      ],
      summary: {
        risk_level: 'low',
        participation: 78,
        sentiment: 74,
        highlights: [
          'Team engagement trending upward week over week',
          'Stress reports declining following wellness initiative',
          'Upcoming leadership AMA scheduled for Friday',
        ],
      },
    };
  }
}

export function requestSlackInstall() {
  window.location.href = `${API_BASE}/integrations/slack/start-install`;
}

export async function sendSlackTest(channel) {
  return apiFetch('/integrations/slack/test', {
    method: 'POST',
    body: JSON.stringify({ channel }),
  });
}

export function goToBilling(plan = 'starter') {
  window.location.href = `${API_BASE}/billing/checkout?plan=${plan}`;
}

export async function requestDevLogin(email) {
  return apiFetch('/auth/request-link-local', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export { API_BASE };
