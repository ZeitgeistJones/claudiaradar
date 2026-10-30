// Research feed + review modal for auto-discovered candidates.
// Newly discovered items stay Needs review until individually checked.

let reviewingId = null;

const reviewBackdrop = document.getElementById('review-backdrop');
const reviewForm = document.getElementById('review-form');
const reviewSummary = document.getElementById('review-summary');
const reviewOpen = document.getElementById('review-open');
const reviewCancel = document.getElementById('review-cancel');

function closeReview() {
  reviewingId = null;
  if (reviewBackdrop) reviewBackdrop.classList.remove('show');
  if (reviewForm) reviewForm.reset();
}

function openReview(entry) {
  if (!reviewBackdrop || !reviewForm || !entry) return;
  reviewingId = entry.id;
  if (reviewSummary) {
    reviewSummary.textContent =
      `${entry.title || 'Untitled'} · ${entry.outlet || 'Unknown'} · ${entry.date || ''}`;
  }
  if (reviewOpen) {
    reviewOpen.href = entry.url || '#';
  }
  reviewForm.elements.tier.value = ['Niche', 'Crossover', 'Mainstream', 'Major'].includes(entry.tier)
    ? entry.tier
    : 'Niche';
  reviewForm.elements.origin.value = ['Independent', 'Fan / community', 'Owned / official'].includes(entry.origin)
    ? entry.origin
    : 'Independent';
  reviewBackdrop.classList.add('show');
}

if (reviewCancel) reviewCancel.onclick = closeReview;
if (reviewBackdrop) {
  reviewBackdrop.onclick = (e) => {
    if (e.target === reviewBackdrop) closeReview();
  };
}
if (reviewForm) {
  reviewForm.onsubmit = (e) => {
    e.preventDefault();
    const found = rows.find((x) => x.id === reviewingId);
    if (!found) {
      closeReview();
      return;
    }
    const data = Object.fromEntries(new FormData(reviewForm));
    if (!data.confirm) {
      alert('Confirm you opened and checked the source.');
      return;
    }
    found.tier = data.tier;
    found.origin = data.origin;
    found.verification = 'Verified';
    found.notes = (found.notes || '') + ' Manually reviewed ' + new Date().toISOString().slice(0, 10) + '.';
    save();
    closeReview();
    render();
  };
}

const oldRender = render;
render = function () {
  oldRender();
  for (const button of document.querySelectorAll('[data-del]')) {
    const found = rows.find((x) => x.id === button.dataset.del);
    if (!found || found.verification !== 'Needs review') continue;
    const verify = document.createElement('button');
    verify.type = 'button';
    verify.className = 'outline';
    verify.textContent = 'Review';
    verify.onclick = () => openReview(found);
    button.before(verify);
  }
};

(async function loadDiscovery() {
  const stamp = document.getElementById('update-status');
  try {
    const response = await fetch('./data/mentions.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('No data file');
    const data = await response.json();
    const incoming = [...(data.verified || []), ...(data.candidates || [])];
    const current = new Set(rows.map((x) => x.url));
    const valid = (x) =>
      x &&
      typeof x.title === 'string' &&
      typeof x.url === 'string' &&
      /^https?:\/\//i.test(x.url) &&
      /^\d{4}-\d{2}-\d{2}$/.test(x.date);
    for (const entry of incoming) {
      if (!valid(entry) || current.has(entry.url)) continue;
      rows.push({ ...entry, id: entry.id || 'feed-' + rows.length });
      current.add(entry.url);
    }
    render();
    if (stamp) {
      stamp.textContent =
        'Source data last refreshed: ' +
        (data.updatedAt ? new Date(data.updatedAt).toLocaleString() : 'unknown') +
        ' · New discoveries require review';
    }
  } catch (err) {
    if (stamp) stamp.textContent = 'Research feed unavailable · Manual entries still work';
  }
})();
