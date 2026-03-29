# EKG MMVT vs PMVT Recognition Drill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-page EKG flashcard drill that tests MMVT vs PMVT recognition with SM-2 spaced repetition, all in one HTML file.

**Architecture:** Single `index.html` with embedded CSS and JS. Four screens (home, card front, card back, session complete) rendered via show/hide. SM-2 algorithm manages card scheduling. State persisted in localStorage. EKG strip images in `images/` folder.

**Tech Stack:** Vanilla HTML, CSS, JavaScript. No framework, no build step, no dependencies.

---

### File Map

| File | Responsibility |
|------|---------------|
| `index.html` | All markup, styles, and JavaScript |
| `images/mmvt-*.svg` | MMVT placeholder EKG strip images (replaced with real PNGs later) |
| `images/pmvt-*.svg` | PMVT placeholder EKG strip images (replaced with real PNGs later) |

---

### Task 1: Project Setup + Base HTML/CSS

**Files:**
- Create: `index.html`

- [ ] **Step 1: Create index.html with all screen containers and dark-theme CSS**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EKG Drill: MMVT vs PMVT</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0d1117;
      color: #e6edf3;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
    }

    .screen { display: none; width: 100%; max-width: 720px; padding: 24px; }
    .screen.active { display: flex; flex-direction: column; align-items: center; }

    h1 { font-size: 1.8rem; font-weight: 600; margin-bottom: 8px; text-align: center; }
    h2 { font-size: 1.3rem; font-weight: 500; margin-bottom: 16px; text-align: center; }

    .stats {
      display: flex;
      gap: 24px;
      margin: 24px 0;
      flex-wrap: wrap;
      justify-content: center;
    }

    .stat {
      text-align: center;
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 12px;
      padding: 16px 24px;
      min-width: 120px;
    }

    .stat-value {
      font-size: 2rem;
      font-weight: 700;
      display: block;
    }

    .stat-label {
      font-size: 0.8rem;
      color: #8b949e;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-top: 4px;
    }

    .btn {
      padding: 14px 32px;
      border: none;
      border-radius: 8px;
      font-size: 1.1rem;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.15s;
    }

    .btn:hover { opacity: 0.85; }

    .btn-primary {
      background: #238636;
      color: #fff;
    }

    .btn-mmvt {
      background: #1f6feb;
      color: #fff;
      flex: 1;
    }

    .btn-pmvt {
      background: #8957e5;
      color: #fff;
      flex: 1;
    }

    .btn-next {
      background: #30363d;
      color: #e6edf3;
      border: 1px solid #484f58;
    }

    .answer-buttons {
      display: flex;
      gap: 16px;
      width: 100%;
      margin-top: 20px;
    }

    .ekg-image {
      width: 100%;
      max-height: 400px;
      object-fit: contain;
      border: 1px solid #21262d;
      border-radius: 8px;
      background: #fff;
    }

    .ekg-image-small {
      width: 100%;
      max-height: 240px;
      object-fit: contain;
      border: 1px solid #21262d;
      border-radius: 8px;
      background: #fff;
      margin-bottom: 16px;
    }

    .progress {
      font-size: 0.85rem;
      color: #8b949e;
      margin-bottom: 16px;
    }

    .banner {
      width: 100%;
      padding: 12px;
      border-radius: 8px;
      text-align: center;
      font-weight: 600;
      font-size: 1.1rem;
      margin-bottom: 16px;
    }

    .banner-correct { background: rgba(63, 185, 80, 0.15); color: #3fb950; border: 1px solid #238636; }
    .banner-incorrect { background: rgba(248, 81, 73, 0.15); color: #f85149; border: 1px solid #da3633; }

    .answer-label {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 12px;
      text-align: center;
    }

    .explanation {
      width: 100%;
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 20px;
    }

    .explanation ul {
      list-style: none;
      padding: 0;
    }

    .explanation li {
      padding: 6px 0;
      padding-left: 20px;
      position: relative;
      font-size: 0.95rem;
      line-height: 1.5;
    }

    .explanation li::before {
      content: "•";
      position: absolute;
      left: 4px;
      color: #8b949e;
    }

    @media (max-width: 480px) {
      .answer-buttons { flex-direction: column; }
      .stats { flex-direction: column; align-items: center; }
      .stat { width: 100%; }
    }
  </style>
</head>
<body>
  <!-- Home Screen -->
  <div id="screen-home" class="screen active">
    <h1>EKG Drill</h1>
    <h2>MMVT vs PMVT</h2>
    <div class="stats">
      <div class="stat">
        <span class="stat-value" id="stat-due">0</span>
        <span class="stat-label">Due Today</span>
      </div>
      <div class="stat">
        <span class="stat-value" id="stat-mastered">0</span>
        <span class="stat-label">Mastered</span>
      </div>
      <div class="stat">
        <span class="stat-value" id="stat-streak">0</span>
        <span class="stat-label">Streak</span>
      </div>
    </div>
    <button class="btn btn-primary" id="btn-start">Start</button>
  </div>

  <!-- Card Front -->
  <div id="screen-front" class="screen">
    <p class="progress" id="card-progress">Card 1 of 10</p>
    <img class="ekg-image" id="ekg-front" src="" alt="EKG Strip">
    <div class="answer-buttons">
      <button class="btn btn-mmvt" id="btn-mmvt">MMVT</button>
      <button class="btn btn-pmvt" id="btn-pmvt">PMVT</button>
    </div>
  </div>

  <!-- Card Back -->
  <div id="screen-back" class="screen">
    <div class="banner" id="result-banner"></div>
    <img class="ekg-image-small" id="ekg-back" src="" alt="EKG Strip">
    <p class="answer-label" id="correct-answer"></p>
    <div class="explanation">
      <ul id="explanation-list"></ul>
    </div>
    <button class="btn btn-next" id="btn-next">Next</button>
  </div>

  <!-- Session Complete -->
  <div id="screen-complete" class="screen">
    <h1>Session Complete</h1>
    <div class="stats">
      <div class="stat">
        <span class="stat-value" id="stat-reviewed">0</span>
        <span class="stat-label">Reviewed</span>
      </div>
      <div class="stat">
        <span class="stat-value" id="stat-accuracy">0%</span>
        <span class="stat-label">Accuracy</span>
      </div>
    </div>
    <button class="btn btn-primary" id="btn-done">Done</button>
  </div>

  <script>
    // JS will go here in subsequent tasks
  </script>
</body>
</html>
```

- [ ] **Step 2: Verify in browser**

Open `index.html` in a browser. You should see the home screen with "EKG Drill / MMVT vs PMVT" title, three stat boxes showing 0, and a green Start button on a dark background.

- [ ] **Step 3: Commit**

```bash
cd "/Users/jasongusdorf/CodingProjects/EKG Website"
git init
git add index.html
git commit -m "feat: base HTML structure with dark theme and four screen containers"
```

---

### Task 2: SM-2 Spaced Repetition Engine

**Files:**
- Modify: `index.html` (script section)

- [ ] **Step 1: Add SM-2 engine functions inside the `<script>` tag**

Replace the `<script>` section in `index.html` with:

```html
<script>
  // ========== SM-2 Spaced Repetition Engine ==========

  const STORAGE_KEY = 'ekg-drill-sr-state';

  let srState = {}; // { cardId: { easeFactor, interval, nextReview, repetitions } }

  function todayStr() {
    return new Date().toISOString().slice(0, 10);
  }

  function addDays(dateStr, days) {
    const d = new Date(dateStr + 'T00:00:00');
    d.setDate(d.getDate() + days);
    return d.toISOString().slice(0, 10);
  }

  function getCardState(cardId) {
    if (!srState[cardId]) {
      srState[cardId] = {
        easeFactor: 2.5,
        interval: 0,
        nextReview: null,
        repetitions: 0
      };
    }
    return srState[cardId];
  }

  function gradeCard(cardId, correct) {
    const s = getCardState(cardId);
    if (correct) {
      s.repetitions++;
      if (s.repetitions === 1) {
        s.interval = 1;
      } else if (s.repetitions === 2) {
        s.interval = 6;
      } else {
        s.interval = Math.round(s.interval * s.easeFactor);
      }
      s.easeFactor = Math.min(3.0, s.easeFactor + 0.1);
    } else {
      s.repetitions = 0;
      s.interval = 1;
      s.easeFactor = Math.max(1.3, s.easeFactor - 0.2);
    }
    s.nextReview = addDays(todayStr(), s.interval);
    saveState();
  }

  function isDue(cardId) {
    const s = srState[cardId];
    if (!s || s.nextReview === null) return false;
    return s.nextReview <= todayStr();
  }

  function isNew(cardId) {
    return !srState[cardId] || srState[cardId].nextReview === null;
  }

  function isMastered(cardId) {
    const s = srState[cardId];
    return s && s.interval >= 21;
  }

  function getSessionQueue(cards) {
    const due = cards.filter(c => isDue(c.id));
    const unseen = cards.filter(c => isNew(c.id));
    return [...due, ...unseen];
  }

  function getStats(cards) {
    const due = cards.filter(c => isDue(c.id)).length;
    const mastered = cards.filter(c => isMastered(c.id)).length;
    const unseen = cards.filter(c => isNew(c.id)).length;
    return { due, mastered, unseen, total: cards.length, dueAndNew: due + unseen };
  }

  // ========== Persistence ==========

  function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(srState));
  }

  function loadState() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try { srState = JSON.parse(raw); } catch (e) { srState = {}; }
    }
  }
</script>
```

- [ ] **Step 2: Verify SM-2 logic in browser console**

Open `index.html`, open DevTools console, and run:

```js
// Test new card state
console.assert(isNew('test-001') === true, 'New card should be new');

// Grade correct
gradeCard('test-001', true);
console.assert(srState['test-001'].interval === 1, 'First correct: interval should be 1');
console.assert(srState['test-001'].repetitions === 1, 'First correct: reps should be 1');

// Grade correct again
gradeCard('test-001', true);
console.assert(srState['test-001'].interval === 6, 'Second correct: interval should be 6');

// Grade correct a third time
gradeCard('test-001', true);
console.assert(srState['test-001'].interval === Math.round(6 * 2.7), 'Third correct: interval should be 6 * 2.7 = 16');

// Grade incorrect resets
gradeCard('test-001', false);
console.assert(srState['test-001'].interval === 1, 'Incorrect: interval should reset to 1');
console.assert(srState['test-001'].repetitions === 0, 'Incorrect: reps should reset to 0');

// Clean up test state
delete srState['test-001'];
saveState();
console.log('All SM-2 tests passed');
```

Expected: "All SM-2 tests passed" with no assertion errors.

- [ ] **Step 3: Commit**

```bash
cd "/Users/jasongusdorf/CodingProjects/EKG Website"
git add index.html
git commit -m "feat: SM-2 spaced repetition engine with localStorage persistence"
```

---

### Task 3: Placeholder EKG Images + Card Data

**Files:**
- Create: `images/mmvt-001.svg`, `images/mmvt-002.svg`, `images/mmvt-003.svg`
- Create: `images/pmvt-001.svg`, `images/pmvt-002.svg`, `images/pmvt-003.svg`
- Modify: `index.html` (add CARDS array to script section)

- [ ] **Step 1: Create placeholder MMVT SVG images**

These are simple placeholder strip images. They'll be replaced with real EKGs later.

Create `images/mmvt-001.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" width="800" height="200">
  <rect width="800" height="200" fill="#fff"/>
  <line x1="0" y1="100" x2="800" y2="100" stroke="#fcc" stroke-width="0.5"/>
  <polyline fill="none" stroke="#222" stroke-width="1.5"
    points="0,100 30,100 35,95 40,100 60,100 65,60 68,140 72,100 100,100
            130,100 135,95 140,100 160,100 165,60 168,140 172,100 200,100
            230,100 235,95 240,100 260,100 265,60 268,140 272,100 300,100
            330,100 335,95 340,100 360,100 365,60 368,140 372,100 400,100
            430,100 435,95 440,100 460,100 465,60 468,140 472,100 500,100
            530,100 535,95 540,100 560,100 565,60 568,140 572,100 600,100
            630,100 635,95 640,100 660,100 665,60 668,140 672,100 700,100
            730,100 735,95 740,100 760,100 765,60 768,140 772,100 800,100"/>
  <text x="400" y="190" text-anchor="middle" fill="#999" font-size="12">MMVT Placeholder 1</text>
</svg>
```

Create `images/mmvt-002.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" width="800" height="200">
  <rect width="800" height="200" fill="#fff"/>
  <line x1="0" y1="100" x2="800" y2="100" stroke="#fcc" stroke-width="0.5"/>
  <polyline fill="none" stroke="#222" stroke-width="1.5"
    points="0,100 25,100 30,90 35,100 50,100 55,50 60,150 65,100 90,100
            115,100 120,90 125,100 140,100 145,50 150,150 155,100 180,100
            205,100 210,90 215,100 230,100 235,50 240,150 245,100 270,100
            295,100 300,90 305,100 320,100 325,50 330,150 335,100 360,100
            385,100 390,90 395,100 410,100 415,50 420,150 425,100 450,100
            475,100 480,90 485,100 500,100 505,50 510,150 515,100 540,100
            565,100 570,90 575,100 590,100 595,50 600,150 605,100 630,100
            655,100 660,90 665,100 680,100 685,50 690,150 695,100 720,100
            745,100 750,90 755,100 770,100 775,50 780,150 785,100 800,100"/>
  <text x="400" y="190" text-anchor="middle" fill="#999" font-size="12">MMVT Placeholder 2</text>
</svg>
```

Create `images/mmvt-003.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" width="800" height="200">
  <rect width="800" height="200" fill="#fff"/>
  <line x1="0" y1="100" x2="800" y2="100" stroke="#fcc" stroke-width="0.5"/>
  <polyline fill="none" stroke="#222" stroke-width="1.5"
    points="0,100 20,100 25,80 32,120 35,100 55,100 60,45 65,155 70,100 95,100
            115,100 120,80 127,120 130,100 150,100 155,45 160,155 165,100 190,100
            210,100 215,80 222,120 225,100 245,100 250,45 255,155 260,100 285,100
            305,100 310,80 317,120 320,100 340,100 345,45 350,155 355,100 380,100
            400,100 405,80 412,120 415,100 435,100 440,45 445,155 450,100 475,100
            495,100 500,80 507,120 510,100 530,100 535,45 540,155 545,100 570,100
            590,100 595,80 602,120 605,100 625,100 630,45 635,155 640,100 665,100
            685,100 690,80 697,120 700,100 720,100 725,45 730,155 735,100 760,100
            780,100 785,80 792,120 795,100 800,100"/>
  <text x="400" y="190" text-anchor="middle" fill="#999" font-size="12">MMVT Placeholder 3</text>
</svg>
```

- [ ] **Step 2: Create placeholder PMVT SVG images**

Create `images/pmvt-001.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" width="800" height="200">
  <rect width="800" height="200" fill="#fff"/>
  <line x1="0" y1="100" x2="800" y2="100" stroke="#fcc" stroke-width="0.5"/>
  <polyline fill="none" stroke="#222" stroke-width="1.5"
    points="0,100 20,100 25,85 30,100 45,100 50,70 55,130 60,100 80,100
            95,100 100,75 108,125 112,100 130,100 135,40 142,160 148,100 170,100
            185,100 192,60 198,140 204,100 225,100 232,30 238,170 244,100 265,100
            280,100 286,55 292,145 298,100 315,100 322,35 328,165 334,100 355,100
            370,100 376,65 382,135 388,100 405,100 412,45 418,155 424,100 445,100
            460,100 466,70 472,130 478,100 498,100 504,50 510,150 516,100 538,100
            555,100 560,80 566,120 572,100 590,100 596,60 602,140 608,100 630,100
            648,100 654,40 660,160 666,100 690,100 696,75 702,125 708,100 730,100
            748,100 754,55 760,145 766,100 800,100"/>
  <text x="400" y="190" text-anchor="middle" fill="#999" font-size="12">PMVT Placeholder 1</text>
</svg>
```

Create `images/pmvt-002.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" width="800" height="200">
  <rect width="800" height="200" fill="#fff"/>
  <line x1="0" y1="100" x2="800" y2="100" stroke="#fcc" stroke-width="0.5"/>
  <polyline fill="none" stroke="#222" stroke-width="1.5"
    points="0,100 15,100 20,90 25,110 30,100 50,100 55,80 62,120 68,85 74,115 80,100
            100,100 108,70 114,130 120,60 126,140 132,100 155,100 162,50 168,150 174,45 180,155 186,100
            210,100 216,65 222,135 228,55 234,145 240,100 260,100 268,75 274,125 280,80 286,120 292,100
            315,100 322,45 328,155 334,40 340,160 346,100 370,100 376,70 382,130 388,65 394,135 400,100
            420,100 428,55 434,145 440,60 446,140 452,100 475,100 482,80 488,120 494,85 500,115 506,100
            530,100 536,50 542,150 548,55 554,145 560,100 585,100 592,75 598,125 604,70 610,130 616,100
            640,100 648,60 654,140 660,45 666,155 672,100 700,100 706,85 712,115 718,90 724,110 730,100
            755,100 762,70 768,130 774,75 780,125 786,100 800,100"/>
  <text x="400" y="190" text-anchor="middle" fill="#999" font-size="12">PMVT Placeholder 2</text>
</svg>
```

Create `images/pmvt-003.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" width="800" height="200">
  <rect width="800" height="200" fill="#fff"/>
  <line x1="0" y1="100" x2="800" y2="100" stroke="#fcc" stroke-width="0.5"/>
  <polyline fill="none" stroke="#222" stroke-width="1.5"
    points="0,100 10,100 15,90 20,100 35,100 40,80 48,120 52,75 58,125 62,100
            80,100 86,60 92,140 98,50 104,150 110,55 116,145 122,100
            145,100 152,40 158,160 164,35 170,165 176,45 182,155 188,100
            210,100 218,30 224,170 230,25 236,175 242,30 248,170 254,100
            275,100 282,45 288,155 294,50 300,150 306,55 312,145 318,100
            340,100 346,65 352,135 358,70 364,130 370,75 376,125 382,100
            400,100 408,80 414,120 420,85 426,115 432,90 438,110 444,100
            465,100 472,85 478,115 484,90 490,110 496,95 502,105 508,100
            530,100 536,90 542,110 548,92 554,108 560,95 566,105 572,100
            595,100 600,95 605,105 610,97 615,103 620,98 625,102 630,100
            660,100 700,100 740,100 780,100 800,100"/>
  <text x="400" y="190" text-anchor="middle" fill="#999" font-size="12">PMVT Placeholder 3 (Torsades pattern)</text>
</svg>
```

- [ ] **Step 3: Add CARDS array to index.html**

Add this at the top of the `<script>` section, before the SM-2 engine code:

```js
// ========== Card Data ==========

const CARDS = [
  {
    id: 'mmvt-001',
    image: 'images/mmvt-001.svg',
    answer: 'mmvt',
    explanationBullets: [
      'Uniform QRS morphology: every complex is identical',
      'Regular R-R intervals throughout the strip',
      'Wide QRS complexes (>120ms) with consistent shape'
    ]
  },
  {
    id: 'mmvt-002',
    image: 'images/mmvt-002.svg',
    answer: 'mmvt',
    explanationBullets: [
      'Monomorphic pattern: QRS complexes do not change beat-to-beat',
      'Consistent axis throughout the tracing',
      'Regular rate with no variation in amplitude'
    ]
  },
  {
    id: 'mmvt-003',
    image: 'images/mmvt-003.svg',
    answer: 'mmvt',
    explanationBullets: [
      'All QRS complexes share the same morphology',
      'No beat-to-beat variation in axis or amplitude',
      'AV dissociation may be present but QRS shape is uniform'
    ]
  },
  {
    id: 'pmvt-001',
    image: 'images/pmvt-001.svg',
    answer: 'pmvt',
    explanationBullets: [
      'QRS morphology varies from beat to beat',
      'Amplitude changes progressively across the strip',
      'Irregular R-R intervals with no repeating pattern'
    ]
  },
  {
    id: 'pmvt-002',
    image: 'images/pmvt-002.svg',
    answer: 'pmvt',
    explanationBullets: [
      'Changing QRS axis: complexes shift direction',
      'No two consecutive beats share the same morphology',
      'Chaotic-appearing rhythm without a consistent bundle branch pattern'
    ]
  },
  {
    id: 'pmvt-003',
    image: 'images/pmvt-003.svg',
    answer: 'pmvt',
    explanationBullets: [
      'Classic Torsades de Pointes: sinusoidal amplitude variation',
      'QRS complexes appear to twist around the baseline',
      'Amplitude waxes and wanes over a run of beats'
    ]
  }
];
```

- [ ] **Step 4: Verify in browser**

Open `index.html`. Open console. Run:

```js
console.log(CARDS.length); // 6
console.log(CARDS[0].id); // "mmvt-001"
```

Verify all 6 SVG images load by temporarily setting `document.querySelector('.ekg-image').src = CARDS[0].image` in the console.

- [ ] **Step 5: Commit**

```bash
cd "/Users/jasongusdorf/CodingProjects/EKG Website"
git add images/ index.html
git commit -m "feat: placeholder EKG strip images and card data array"
```

---

### Task 4: App State + Screen Routing + Full Drill Flow

**Files:**
- Modify: `index.html` (script section)

- [ ] **Step 1: Add app state, screen routing, and all event handlers after the persistence functions**

```js
// ========== App State ==========

let app = {
  screen: 'home',
  sessionQueue: [],
  currentIndex: 0,
  sessionCorrect: 0,
  sessionTotal: 0,
  streak: 0
};

// ========== Screen Routing ==========

function showScreen(name) {
  app.screen = name;
  document.querySelectorAll('.screen').forEach(function(s) {
    s.classList.remove('active');
  });
  document.getElementById('screen-' + name).classList.add('active');
}

// ========== Home Screen ==========

function renderHome() {
  loadState();
  var stats = getStats(CARDS);
  document.getElementById('stat-due').textContent = stats.dueAndNew;
  document.getElementById('stat-mastered').textContent = stats.mastered;
  document.getElementById('stat-streak').textContent = app.streak;

  var startBtn = document.getElementById('btn-start');
  startBtn.disabled = stats.dueAndNew === 0;
  startBtn.textContent = stats.dueAndNew === 0 ? 'All caught up!' : 'Start';
  if (stats.dueAndNew === 0) {
    startBtn.style.opacity = '0.5';
    startBtn.style.cursor = 'default';
  } else {
    startBtn.style.opacity = '1';
    startBtn.style.cursor = 'pointer';
  }
}

// ========== Card Screens ==========

function showCardFront() {
  var card = app.sessionQueue[app.currentIndex];
  document.getElementById('card-progress').textContent =
    'Card ' + (app.currentIndex + 1) + ' of ' + app.sessionQueue.length;
  document.getElementById('ekg-front').src = card.image;
  showScreen('front');
}

function showCardBack(card, correct) {
  var banner = document.getElementById('result-banner');
  banner.textContent = correct ? 'Correct' : 'Incorrect';
  banner.className = 'banner ' + (correct ? 'banner-correct' : 'banner-incorrect');

  document.getElementById('ekg-back').src = card.image;
  document.getElementById('correct-answer').textContent =
    'Answer: ' + card.answer.toUpperCase();

  var list = document.getElementById('explanation-list');
  while (list.firstChild) {
    list.removeChild(list.firstChild);
  }
  card.explanationBullets.forEach(function(bullet) {
    var li = document.createElement('li');
    li.textContent = bullet;
    list.appendChild(li);
  });

  showScreen('back');
}

function showComplete() {
  var pct = app.sessionTotal > 0
    ? Math.round((app.sessionCorrect / app.sessionTotal) * 100)
    : 0;
  document.getElementById('stat-reviewed').textContent = app.sessionTotal;
  document.getElementById('stat-accuracy').textContent = pct + '%';
  showScreen('complete');
}

// ========== Event Handlers ==========

function handleStart() {
  var queue = getSessionQueue(CARDS);
  if (queue.length === 0) return;
  app.sessionQueue = queue;
  app.currentIndex = 0;
  app.sessionCorrect = 0;
  app.sessionTotal = 0;
  showCardFront();
}

function handleAnswer(answer) {
  var card = app.sessionQueue[app.currentIndex];
  var correct = answer === card.answer;
  gradeCard(card.id, correct);
  app.sessionTotal++;
  if (correct) {
    app.sessionCorrect++;
    app.streak++;
  } else {
    app.streak = 0;
  }
  showCardBack(card, correct);
}

function handleNext() {
  app.currentIndex++;
  if (app.currentIndex >= app.sessionQueue.length) {
    showComplete();
  } else {
    showCardFront();
  }
}

function handleDone() {
  renderHome();
  showScreen('home');
}

// ========== Init ==========

function init() {
  loadState();

  document.getElementById('btn-start').addEventListener('click', handleStart);
  document.getElementById('btn-mmvt').addEventListener('click', function() { handleAnswer('mmvt'); });
  document.getElementById('btn-pmvt').addEventListener('click', function() { handleAnswer('pmvt'); });
  document.getElementById('btn-next').addEventListener('click', handleNext);
  document.getElementById('btn-done').addEventListener('click', handleDone);

  document.addEventListener('keydown', function(e) {
    if (app.screen === 'front') {
      if (e.key === '1' || e.key === 'm') handleAnswer('mmvt');
      if (e.key === '2' || e.key === 'p') handleAnswer('pmvt');
    } else if (app.screen === 'back') {
      if (e.key === ' ' || e.key === 'Enter') handleNext();
    } else if (app.screen === 'home') {
      if (e.key === ' ' || e.key === 'Enter') handleStart();
    } else if (app.screen === 'complete') {
      if (e.key === ' ' || e.key === 'Enter') handleDone();
    }
  });

  renderHome();
  showScreen('home');
}

document.addEventListener('DOMContentLoaded', init);
```

- [ ] **Step 2: Verify the full flow in browser**

1. Open `index.html` in browser
2. Home screen should show "Due Today: 6" (all cards are new/unseen)
3. Click "Start"
4. Card front: see an EKG strip image with MMVT and PMVT buttons
5. Click an answer
6. Card back: see Correct/Incorrect banner, explanation bullets, Next button
7. Click through all 6 cards
8. Session complete: see cards reviewed and accuracy percentage
9. Click "Done", return to home
10. Refresh browser: due count changes based on scheduling (cards answered correctly today won't be due until tomorrow)

- [ ] **Step 3: Verify keyboard shortcuts**

1. Press Space/Enter on home screen to start
2. Press 1 or M for MMVT, 2 or P for PMVT on card front
3. Press Space/Enter on card back to advance
4. Press Space/Enter on complete screen to return home

- [ ] **Step 4: Commit**

```bash
cd "/Users/jasongusdorf/CodingProjects/EKG Website"
git add index.html
git commit -m "feat: complete drill flow with app state, screen routing, keyboard shortcuts"
```

---

### Task 5: Source Real EKG Images

**Files:**
- Create: real EKG image files in `images/`
- Modify: `index.html` (update CARDS array)

- [ ] **Step 1: Source open-access EKG strip images**

Find and download ~20 EKG strip images (roughly 10 MMVT, 10 PMVT) from these open-access sources:

- **LITFL** (litfl.com/ecg-library): CC-licensed EKG examples
- **ECGpedia** (ecgpedia.org): wiki-style EKG database
- **Wikimedia Commons**: search "monomorphic ventricular tachycardia" and "polymorphic ventricular tachycardia"
- **PhysioNet** (physionet.org): open EKG databases

Save each image to `images/` with naming convention:
- `mmvt-001.png` through `mmvt-010.png`
- `pmvt-001.png` through `pmvt-010.png`

Delete the placeholder SVG files.

- [ ] **Step 2: Update CARDS array with real image paths and clinical explanations**

Replace the CARDS array with entries pointing to the real images. Each card needs explanation bullets specific to that strip's visible features. Example for a real strip:

```js
{
  id: 'mmvt-001',
  image: 'images/mmvt-001.png',
  answer: 'mmvt',
  explanationBullets: [
    'Uniform QRS morphology: every complex shares the same shape and width',
    'Regular R-R intervals at approximately 180 bpm',
    'RBBB morphology in V1 with leftward axis suggesting LV origin',
    'No beat-to-beat variation in amplitude or axis'
  ]
}
```

Write clinically accurate bullets for each strip based on what is visible in that specific EKG.

- [ ] **Step 3: Verify all images load**

Open `index.html` and click through all cards. Confirm:
- Every image loads (no broken image icons)
- Images are readable at the display size
- Explanation bullets are accurate for each strip

- [ ] **Step 4: Commit**

```bash
cd "/Users/jasongusdorf/CodingProjects/EKG Website"
git add images/ index.html
git rm images/*.svg
git commit -m "feat: real EKG strip images with clinical explanations"
```

---

### Task 6: Reset Button + Final Polish

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add a reset button to the home screen HTML**

Add this button in the HTML, below the Start button inside `screen-home`:

```html
<button class="btn btn-next" id="btn-reset" style="margin-top: 12px; font-size: 0.85rem;">Reset Progress</button>
```

- [ ] **Step 2: Add reset handler to the init function**

Add to the event listeners in `init`:

```js
document.getElementById('btn-reset').addEventListener('click', handleReset);
```

Add the handler function before `init`:

```js
function handleReset() {
  if (confirm('Reset all progress? This cannot be undone.')) {
    srState = {};
    saveState();
    app.streak = 0;
    renderHome();
  }
}
```

- [ ] **Step 3: Test on mobile viewport**

Open browser DevTools, toggle device toolbar, test at 375px width (iPhone SE). Check:
- Buttons stack vertically and remain tappable
- EKG images scale without horizontal overflow
- Stats cards stack vertically
- Text remains readable

- [ ] **Step 4: Verify reset**

1. Drill some cards so progress exists
2. Click Reset Progress
3. Confirm dialog appears
4. After confirming: due count returns to total card count, mastered shows 0, streak shows 0

- [ ] **Step 5: Commit**

```bash
cd "/Users/jasongusdorf/CodingProjects/EKG Website"
git add index.html
git commit -m "feat: reset progress button and mobile polish"
```
