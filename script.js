async function updateDashboard() {
  const response = await fetch('/api/dashboard');
  const data = await response.json();

  document.getElementById('totalMinutes').textContent = `${data.total_minutes}`;
  document.getElementById('totalSessions').textContent = `${data.total_sessions}`;
  document.getElementById('streakDays').textContent = `${data.streak} days`;
  document.getElementById('completionRate').textContent = `${data.completion_percent}%`;
}

const greeting = document.getElementById('greeting');
const liveDate = document.getElementById('liveDate');
const liveClock = document.getElementById('liveClock');
const themeToggle = document.getElementById('themeToggle');
const themeIcon = themeToggle.querySelector('.theme-icon');
const timerDisplay = document.getElementById('timerDisplay');
const timerStatus = document.getElementById('timerStatus');
const timerRing = document.getElementById('timerRing');
const timerStart = document.getElementById('timerStart');
const timerReset = document.getElementById('timerReset');
const presets = document.querySelectorAll('.preset');

let timerSeconds = 25 * 60;
let timerTotalSeconds = timerSeconds;
let timerInterval = null;

function updateTime() {
  const now = new Date();
  const hour = now.getHours();
  const greetingText = hour < 12 ? 'Good morning, learner.' : hour < 18 ? 'Good afternoon, learner.' : 'Good evening, learner.';
  greeting.textContent = greetingText;
  liveDate.textContent = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
  liveClock.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function renderTimer() {
  const minutes = Math.floor(timerSeconds / 60).toString().padStart(2, '0');
  const seconds = (timerSeconds % 60).toString().padStart(2, '0');
  timerDisplay.textContent = `${minutes}:${seconds}`;
  const progress = ((timerTotalSeconds - timerSeconds) / timerTotalSeconds) * 100;
  timerRing.style.setProperty('--progress', `${progress}%`);
}

function stopTimer(message) {
  clearInterval(timerInterval);
  timerInterval = null;
  timerStart.textContent = 'Start focus';
  timerStatus.textContent = message;
}

themeToggle.addEventListener('click', () => {
  const isDark = document.body.classList.toggle('dark-mode');
  localStorage.setItem('japanese-study-theme', isDark ? 'dark' : 'light');
  themeIcon.textContent = isDark ? '\u2600' : '\u263e';
  themeToggle.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
});

if (localStorage.getItem('japanese-study-theme') === 'dark') {
  document.body.classList.add('dark-mode');
  themeIcon.textContent = '\u2600';
  themeToggle.setAttribute('aria-label', 'Switch to light mode');
}

timerStart.addEventListener('click', () => {
  if (timerInterval) {
    stopTimer('Focus paused. Come back when you are ready.');
    return;
  }
  timerStart.textContent = 'Pause';
  timerStatus.textContent = 'You are in a focus session. Keep going.';
  timerInterval = setInterval(() => {
    timerSeconds -= 1;
    renderTimer();
    if (timerSeconds <= 0) {
      stopTimer('Session complete. Nice work today.');
        timerRing.classList.add('complete');
      timerSeconds = 0;
      renderTimer();
    }
  }, 1000);
});

timerReset.addEventListener('click', () => {
  stopTimer('Choose a session length and begin when you are ready.');
  timerRing.classList.remove('complete');
  timerSeconds = timerTotalSeconds;
  renderTimer();
});

presets.forEach((preset) => {
  preset.addEventListener('click', () => {
    stopTimer('Choose a session length and begin when you are ready.');
    timerRing.classList.remove('complete');
    timerTotalSeconds = Number(preset.dataset.minutes) * 60;
    timerSeconds = timerTotalSeconds;
    presets.forEach((item) => item.classList.remove('active'));
    preset.classList.add('active');
    renderTimer();
  });
});

updateTime();
renderTimer();
setInterval(updateTime, 1000);
setInterval(updateDashboard, 10000);
