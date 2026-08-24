async function updateDashboard() {
  const response = await fetch('/api/dashboard');
  const data = await response.json();

  document.getElementById('totalMinutes').textContent = `${data.total_minutes}`;
  document.getElementById('totalSessions').textContent = `${data.total_sessions}`;
  document.getElementById('streakDays').textContent = `${data.streak} days`;
  document.body.dataset.streak = data.streak;
  document.getElementById('completionRate').textContent = `${data.completion_percent}%`;
  document.getElementById('topCategory').textContent = data.top_category.replace(/\b\w/g, (letter) => letter.toUpperCase());
  activityData = data;
  renderActivityChart(data[activeRange === 'week' ? 'weekly_activity' : 'monthly_activity']);
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
const themeSwatches = document.querySelectorAll('.theme-swatch');
const petThemeToggle = document.getElementById('petThemeToggle');
const kanaThemeToggle = document.getElementById('kanaThemeToggle');
const petBanner = document.getElementById('petBanner');
const chartRanges = document.querySelectorAll('.chart-range');
const activityHeading = document.getElementById('activityHeading');
>>>>>>>  Stashed changes
let streak = Number(document.body.dataset.streak || 0);
let activeRange = 'week';
let activityData = { weekly_activity: [], monthly_activity: [] };
let timerSeconds = 25 * 60;
let timerTotalSeconds = timerSeconds;
let timerInterval = null;

function renderActivityChart(activity) {
  const chart = document.getElementById('activityChart');
  if (!chart || !activity || !activity.length) {
    return;
  }

  const maxMinutes = Math.max(...activity.map((day) => day.minutes), 1);
  chart.classList.toggle('month-view', activeRange === 'month');
  chart.innerHTML = activity
    .map(
      (day) => `
        <div class="chart-column${day.date === new Date().toISOString().slice(0, 10) ? ' today' : ''}" title="${day.date}: ${day.minutes} minutes">
          <div class="bar-track"><div class="activity-bar" style="height: ${Math.max((day.minutes / maxMinutes) * 100, 4)}%"></div></div>
          <strong>${day.minutes}</strong>
          <span>${day.label}</span>
        </div>
      `,
    )
    .join('');
}

chartRanges.forEach((rangeButton) => {
  rangeButton.addEventListener('click', () => {
    activeRange = rangeButton.dataset.range;
    chartRanges.forEach((item) => item.classList.toggle('active', item === rangeButton));
    activityHeading.textContent = activeRange === 'week' ? 'Last 7 days' : 'Last 30 days';
    renderActivityChart(activityData[activeRange === 'week' ? 'weekly_activity' : 'monthly_activity']);
  });
});

function updateTime() {
  const now = new Date();
  const hour = now.getHours();
  streak = Number(document.body.dataset.streak || 0);
  const greetingText = hour < 12 ? 'Good morning, learner.' : hour < 18 ? 'Good afternoon, learner.' : 'Good evening, learner.';
  greeting.textContent = streak ? `${greetingText} You are on a ${streak}-day streak.` : greetingText;
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

function applyDarkMode(enabled) {
  document.body.classList.toggle('dark-mode', enabled);
  localStorage.setItem('japanese-study-theme', enabled ? 'dark' : 'light');
  themeIcon.textContent = enabled ? '\u2600' : '\u263e';
  themeToggle.setAttribute('aria-label', enabled ? 'Switch to light mode' : 'Switch to dark mode');
}

themeToggle.addEventListener('click', () => {
  applyDarkMode(!document.body.classList.contains('dark-mode'));
});

function applyColorTheme(theme) {
  document.body.dataset.colorTheme = theme;
  localStorage.setItem('japanese-study-color-theme', theme);
  themeSwatches.forEach((swatch) => swatch.classList.toggle('active', swatch.dataset.theme === theme));
}

themeSwatches.forEach((swatch) => {
  swatch.addEventListener('click', () => applyColorTheme(swatch.dataset.theme));
});

applyColorTheme(localStorage.getItem('japanese-study-color-theme') || 'moss');
applyDarkMode(localStorage.getItem('japanese-study-theme') === 'dark');

function setThemeToggleState(toggle, enabled) {
  toggle.setAttribute('aria-pressed', enabled ? 'true' : 'false');
  toggle.classList.toggle('active', enabled);
}

function applyPetTheme(enabled) {
  document.body.classList.toggle('pet-theme', enabled);
  if (petBanner) {
    petBanner.setAttribute('aria-hidden', enabled ? 'false' : 'true');
  }
  localStorage.setItem('japanese-study-pet-theme', enabled ? 'on' : 'off');
  setThemeToggleState(petThemeToggle, enabled);
}

function applyKanaTheme(enabled) {
  document.body.classList.toggle('kana-theme', enabled);
  localStorage.setItem('japanese-study-kana-theme', enabled ? 'on' : 'off');
  setThemeToggleState(kanaThemeToggle, enabled);
}

petThemeToggle.addEventListener('click', () => applyPetTheme(!document.body.classList.contains('pet-theme')));
kanaThemeToggle.addEventListener('click', () => applyKanaTheme(!document.body.classList.contains('kana-theme')));
applyPetTheme(localStorage.getItem('japanese-study-pet-theme') === 'on');
applyKanaTheme(localStorage.getItem('japanese-study-kana-theme') === 'on');

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
updateDashboard();
setInterval(updateTime, 1000);
setInterval(updateDashboard, 10000);
