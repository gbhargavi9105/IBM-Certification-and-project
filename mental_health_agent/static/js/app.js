/* ═══════════════════════════════════════════════════════
   Serene — Mental Health Agent · JavaScript
   ═══════════════════════════════════════════════════════ */

'use strict';

// ─── State ────────────────────────────────────────────────────────────────────
let sessionId = null;
let isTyping = false;
let breathingInterval = null;
let breathingTimeout = null;
let currentCrisisLevel = 'NONE';
let messageCount = 0;

// ─── DOM references ───────────────────────────────────────────────────────────
const messagesArea    = document.getElementById('messages-area');
const chatContainer   = document.getElementById('chat-container');
const welcomeScreen   = document.getElementById('welcome-screen');
const messageInput    = document.getElementById('message-input');
const sendBtn         = document.getElementById('send-btn');
const typingIndicator = document.getElementById('typing-indicator');
const charCount       = document.getElementById('char-count');
const crisisIndicator = document.getElementById('crisis-indicator');
const crisisLabel     = document.getElementById('crisis-label');
const emergencyBanner = document.getElementById('emergency-banner');
const emergencyText   = document.getElementById('emergency-text');

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSession();
  setupInputListeners();
});

async function initSession() {
  try {
    const res = await fetch('/api/session/new', { method: 'POST' });
    const data = await res.json();
    sessionId = data.session_id;
    console.log('Session started:', sessionId.slice(0, 8));
  } catch (e) {
    sessionId = 'local-' + Date.now();
    console.warn('Session init failed, using local ID');
  }
}

// ─── Input listeners ─────────────────────────────────────────────────────────
function setupInputListeners() {
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  messageInput.addEventListener('input', () => {
    // Auto-resize
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
    // Char count
    const len = messageInput.value.length;
    charCount.textContent = len + ' / 2000';
    charCount.style.color = len > 1800 ? '#f87171' : '';
  });
}

// ─── Send message ─────────────────────────────────────────────────────────────
async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || isTyping) return;

  // Hide welcome screen
  if (welcomeScreen) welcomeScreen.style.display = 'none';

  // Add user message
  appendMessage('user', text);
  messageInput.value = '';
  messageInput.style.height = 'auto';
  charCount.textContent = '0 / 2000';

  // Show typing
  setTyping(true);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });

    if (!res.ok) throw new Error('Server error: ' + res.status);
    const data = await res.json();

    setTyping(false);

    // Update session id (in case it changed)
    if (data.session_id) sessionId = data.session_id;

    // Update crisis indicator
    updateCrisisIndicator(data.crisis_level);
    messageCount = data.message_count || messageCount + 1;

    // Emergency banner
    if (data.emergency_banner) {
      showEmergencyBanner(data.emergency_text);
    }

    // Append AI response
    appendAIMessage(data);

  } catch (e) {
    setTyping(false);
    appendMessage('ai', '⚠️ Something went wrong connecting to Serene. If you\'re in crisis, please call or text **988** immediately — they\'re available 24/7.');
    console.error('Chat error:', e);
  }
}

function sendQuickMessage(msg) {
  messageInput.value = msg;
  sendMessage();
}

// ─── Append messages ──────────────────────────────────────────────────────────
function appendMessage(role, text) {
  const row = document.createElement('div');
  row.className = 'message-row ' + role;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'user' ? '🧑' : '🌿';

  const content = document.createElement('div');
  content.className = 'msg-content';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = formatMessage(text);

  const time = document.createElement('div');
  time.className = 'msg-time';
  time.textContent = formatTime(new Date());

  content.appendChild(bubble);
  content.appendChild(time);
  row.appendChild(avatar);
  row.appendChild(content);
  messagesArea.appendChild(row);
  scrollToBottom();
  return row;
}

function appendAIMessage(data) {
  const row = document.createElement('div');
  row.className = 'message-row ai';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = '🌿';

  const content = document.createElement('div');
  content.className = 'msg-content';

  // Main bubble
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = formatMessage(data.response);
  content.appendChild(bubble);

  // Affirmation badge
  if (data.affirmation) {
    const badge = document.createElement('div');
    badge.className = 'affirmation-badge';
    badge.textContent = '✦ ' + data.affirmation;
    content.appendChild(badge);
  }

  // Psychoeducation
  if (data.psychoeducation) {
    const edu = document.createElement('div');
    edu.className = 'msg-bubble';
    edu.style.cssText = 'margin-top:6px; background: var(--teal-soft); border-color: var(--teal); font-size:13.5px;';
    edu.innerHTML = formatMessage(data.psychoeducation);
    content.appendChild(edu);
  }

  // Inline resources (for CRITICAL/HIGH/MODERATE)
  if (data.show_resources && data.resources) {
    const resCard = buildResourceCard(data.resources);
    if (resCard) content.appendChild(resCard);
  }

  // Timestamp
  const time = document.createElement('div');
  time.className = 'msg-time';
  time.textContent = formatTime(new Date());
  content.appendChild(time);

  row.appendChild(avatar);
  row.appendChild(content);
  messagesArea.appendChild(row);
  scrollToBottom();
}

function buildResourceCard(resources) {
  if (!resources) return null;
  const card = document.createElement('div');
  card.className = 'inline-resource';

  const title = document.createElement('div');
  title.className = 'inline-resource-title';
  title.textContent = resources.message || 'Support Resources';
  card.appendChild(title);

  const allResources = [...(resources.hotlines || []), ...(resources.support || [])];
  allResources.slice(0, 4).forEach(r => {
    const item = document.createElement('div');
    item.className = 'resource-item';
    item.innerHTML = `
      <div class="resource-icon">${r.category === 'crisis' ? '📞' : '💙'}</div>
      <div class="resource-details">
        <div class="r-name">${escapeHtml(r.name)}</div>
        <div class="r-contact">${escapeHtml(r.contact)}</div>
        <div class="r-desc">${escapeHtml(r.description)}</div>
        <div class="r-hours">⏰ ${escapeHtml(r.available)}</div>
      </div>
    `;
    card.appendChild(item);
  });
  return card;
}

// ─── Crisis indicator ─────────────────────────────────────────────────────────
function updateCrisisIndicator(level) {
  currentCrisisLevel = level || 'NONE';
  crisisIndicator.className = 'crisis-indicator';

  const labels = {
    NONE:     { text: 'Feeling okay',     cls: '' },
    LOW:      { text: 'Some distress',    cls: 'level-low' },
    MODERATE: { text: 'Needs support',    cls: 'level-moderate' },
    HIGH:     { text: 'High distress',    cls: 'level-high' },
    CRITICAL: { text: '⚠ Urgent support', cls: 'level-critical' },
  };

  const info = labels[level] || labels.NONE;
  crisisLabel.textContent = info.text;
  if (info.cls) crisisIndicator.classList.add(info.cls);
}

// ─── Emergency banner ─────────────────────────────────────────────────────────
function showEmergencyBanner(text) {
  emergencyText.textContent = text;
  emergencyBanner.classList.remove('hidden');
}
function dismissBanner() {
  emergencyBanner.classList.add('hidden');
}

// ─── Typing state ─────────────────────────────────────────────────────────────
function setTyping(state) {
  isTyping = state;
  sendBtn.disabled = state;
  typingIndicator.classList.toggle('hidden', !state);
  if (state) scrollToBottom();
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('open');
}

// ─── New chat ─────────────────────────────────────────────────────────────────
async function startNewChat() {
  if (isTyping) return;

  // Clear messages
  messagesArea.innerHTML = '';
  welcomeScreen.style.display = '';
  updateCrisisIndicator('NONE');
  emergencyBanner.classList.add('hidden');
  messageCount = 0;

  // New session
  await initSession();

  // Close sidebar on mobile
  document.getElementById('sidebar').classList.remove('open');
}

// ─── Breathing exercise ───────────────────────────────────────────────────────
function openBreathingExercise() {
  document.getElementById('breathing-modal').classList.remove('hidden');
  resetBreathingUI();
  document.getElementById('sidebar').classList.remove('open');
}

function resetBreathingUI() {
  document.getElementById('breath-phase').textContent = 'Ready';
  document.getElementById('breath-count').textContent = '4';
  document.getElementById('cycle-num').textContent = '0';
  const circle = document.getElementById('breathing-circle');
  circle.className = 'breathing-circle';
  ['step-inhale','step-hold1','step-exhale','step-hold2'].forEach((id, i) => {
    document.getElementById(id).className = 'step' + (i === 0 ? ' active' : '');
  });
}

let breathCycle = 0;
let breathRunning = false;

function startBreathing() {
  if (breathRunning) return;
  breathRunning = true;
  breathCycle = 0;
  document.getElementById('breath-start-btn').disabled = true;
  runBreathCycle();
}

function stopBreathing() {
  breathRunning = false;
  clearTimeout(breathingTimeout);
  clearInterval(breathingInterval);
  resetBreathingUI();
  document.getElementById('breath-start-btn').disabled = false;
}

async function runBreathCycle() {
  if (!breathRunning) return;

  const phases = [
    { name: 'Inhale', cls: 'inhale', step: 'step-inhale', duration: 4 },
    { name: 'Hold', cls: '', step: 'step-hold1', duration: 4 },
    { name: 'Exhale', cls: 'exhale', step: 'step-exhale', duration: 4 },
    { name: 'Hold', cls: '', step: 'step-hold2', duration: 4 },
  ];

  const circle = document.getElementById('breathing-circle');
  const phaseEl = document.getElementById('breath-phase');
  const countEl = document.getElementById('breath-count');
  const cycleEl = document.getElementById('cycle-num');

  for (const phase of phases) {
    if (!breathRunning) return;

    // Update step highlights
    ['step-inhale','step-hold1','step-exhale','step-hold2'].forEach(id => {
      document.getElementById(id).className = 'step';
    });
    document.getElementById(phase.step).className = 'step active';

    // Update circle
    circle.className = 'breathing-circle ' + phase.cls;
    phaseEl.textContent = phase.name;

    // Countdown
    for (let i = phase.duration; i >= 1; i--) {
      if (!breathRunning) return;
      countEl.textContent = i;
      await sleep(1000);
    }
  }

  breathCycle++;
  cycleEl.textContent = breathCycle;

  if (breathCycle >= 4) {
    phaseEl.textContent = 'Done ✓';
    countEl.textContent = '🌿';
    circle.className = 'breathing-circle';
    breathRunning = false;
    document.getElementById('breath-start-btn').disabled = false;
  } else {
    runBreathCycle();
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ─── Hotlines modal ───────────────────────────────────────────────────────────
async function showHotlines() {
  document.getElementById('hotlines-modal').classList.remove('hidden');
  document.getElementById('sidebar').classList.remove('open');

  const content = document.getElementById('hotlines-content');
  content.innerHTML = '<div class="loading-spinner">Loading resources...</div>';

  try {
    // Static hotlines data (no need for extra API call)
    const hotlines = [
      { name: '988 Suicide & Crisis Lifeline', contact: 'Call or text 988', desc: 'Free, confidential support for people in suicidal crisis or emotional distress.', hours: '24/7', urgent: true },
      { name: 'Crisis Text Line', contact: 'Text HOME to 741741', desc: 'Free crisis counseling via text message.', hours: '24/7', urgent: true },
      { name: 'SAMHSA National Helpline', contact: '1-800-662-4357', desc: 'Free treatment referrals for mental health and substance use.', hours: '24/7', urgent: true },
      { name: 'Veterans Crisis Line', contact: 'Call 988 press 1 · Text 838255', desc: 'For veterans and service members in crisis.', hours: '24/7', urgent: false },
      { name: 'Trevor Project (LGBTQ+)', contact: '1-866-488-7386 · Text START to 678-678', desc: 'Crisis intervention for LGBTQ+ young people.', hours: '24/7', urgent: false },
      { name: 'Trans Lifeline', contact: '877-565-8860', desc: 'Peer support hotline by and for trans people.', hours: '24/7', urgent: false },
      { name: 'NAMI Helpline', contact: '1-800-950-6264 · Text NAMI to 741741', desc: 'Support, info, and referrals for mental health conditions.', hours: 'Mon–Fri 10am–10pm ET', urgent: false },
      { name: '7 Cups (online)', contact: 'www.7cups.com', desc: 'Free emotional support from trained listeners.', hours: '24/7 online', urgent: false },
    ];

    let html = '<div class="hotlines-section-title">🆘 Immediate Crisis Lines</div>';
    hotlines.filter(h => h.urgent).forEach(h => {
      html += buildHotlineCard(h);
    });
    html += '<div class="hotlines-section-title" style="margin-top:18px">💙 Additional Support</div>';
    hotlines.filter(h => !h.urgent).forEach(h => {
      html += buildHotlineCard(h);
    });

    content.innerHTML = html;
  } catch (e) {
    content.innerHTML = '<p style="color:var(--text-muted);font-size:13px">Could not load resources. Please call 988 if you need immediate help.</p>';
  }
}

function buildHotlineCard(h) {
  return `
    <div class="hotline-card ${h.urgent ? 'urgent' : ''}">
      <div class="hotline-name">${escapeHtml(h.name)}</div>
      <div class="hotline-contact">${escapeHtml(h.contact)}</div>
      <div class="hotline-desc">${escapeHtml(h.desc)}</div>
      <div class="hotline-hours">⏰ ${escapeHtml(h.hours)}</div>
    </div>
  `;
}

// ─── Grounding ────────────────────────────────────────────────────────────────
function showGroundingTechnique() {
  document.getElementById('grounding-modal').classList.remove('hidden');
  document.getElementById('sidebar').classList.remove('open');
}

// ─── Modal helpers ────────────────────────────────────────────────────────────
function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
  if (id === 'breathing-modal') stopBreathing();
}

function closeResourcePanel() {
  document.getElementById('resources-panel').classList.add('hidden');
}

// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      const modal = overlay.id;
      closeModal(modal);
    }
  });
});

// ─── Formatting helpers ───────────────────────────────────────────────────────
function formatMessage(text) {
  if (!text) return '';
  let t = escapeHtml(text);

  // Bold **text**
  t = t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic *text*
  t = t.replace(/\*(.+?)\*/g, '<em>$1</em>');
  // Bullet lists
  t = t.replace(/^[•\-]\s(.+)/gm, '<li>$1</li>');
  t = t.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
  // Numbered lines
  t = t.replace(/^\d+\.\s(.+)/gm, '<li>$1</li>');
  // Line breaks
  t = t.replace(/\n{2,}/g, '</p><p>');
  t = t.replace(/\n/g, '<br>');
  if (!t.startsWith('<')) t = '<p>' + t + '</p>';

  return t;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatTime(date) {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
}

function scrollToBottom() {
  setTimeout(() => {
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }, 50);
}
