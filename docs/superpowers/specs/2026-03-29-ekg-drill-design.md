# EKG MMVT vs PMVT Recognition Drill

## Overview

A single-page web application for board exam prep that drills recognition of Monomorphic Ventricular Tachycardia (MMVT) vs Polymorphic Ventricular Tachycardia (PMVT) from EKG strips. Uses spaced repetition to prioritize strips the user gets wrong.

## Audience

Medical students and residents preparing for USMLE Step 2/3 and IM board exams.

## Tech Stack

- Single `index.html` file (HTML + CSS + JS, no framework, no build step)
- Images in an `images/` folder alongside the HTML
- `localStorage` for spaced repetition state
- No server, no accounts, no dependencies

## Architecture

Three layers inside one file:

### 1. Data Layer

A JavaScript array of card objects:

```js
{
  id: "mmvt-001",
  image: "images/mmvt-001.png",
  answer: "mmvt",          // "mmvt" or "pmvt"
  explanationBullets: [
    "Uniform QRS morphology throughout",
    "Regular R-R intervals",
    "AV dissociation visible in lead II"
  ]
}
```

### 2. Spaced Repetition Engine (SM-2)

Per-card state stored in `localStorage`:

```js
{
  cardId: "mmvt-001",
  easeFactor: 2.5,     // starts at 2.5
  interval: 1,         // days until next review
  nextReview: "2026-03-30",
  repetitions: 0
}
```

Algorithm:
- **Correct answer**: repetitions++. If repetitions == 1, interval = 1. If repetitions == 2, interval = 6. Otherwise, interval = interval * easeFactor. Ease factor increases by 0.1 (max 3.0).
- **Incorrect answer**: repetitions reset to 0, interval reset to 1, ease factor decreases by 0.2 (minimum 1.3).
- Cards sorted by next review date. Overdue cards surface first. New (unseen) cards fill in after all due cards are reviewed.

### 3. UI

Four screens, all rendered in the same page via show/hide:

#### Home Screen
- Title: "EKG Drill: MMVT vs PMVT"
- Stats: cards due today, total cards mastered (interval >= 21 days), current streak (consecutive correct)
- "Start" button

#### Card Front
- EKG strip image, large, filling most of the viewport
- Two buttons at bottom: "MMVT" and "PMVT"
- Progress indicator: "Card 3 of 12"

#### Card Back
- Correct/incorrect banner (green/red) at top
- EKG strip image (reduced size)
- Correct answer label
- 3-4 explanation bullets specific to that strip
- "Next" button

#### Session Complete
- Cards reviewed count
- Accuracy percentage
- "Done" button returns to home

## Visual Design

- Dark background (#0d1117)
- Card panels with subtle border (#21262d)
- White text, green for correct (#3fb950), red for incorrect (#f85149)
- Large image display: strips need to be readable
- Mobile-responsive: buttons stack vertically on small screens, image scales
- Clean, clinical feel. No gamification beyond streak count.

## Content

~20-30 EKG strips, roughly even split between MMVT and PMVT. Sourced from open-access medical image libraries:

- LITFL (Life in the Fast Lane)
- ECGpedia
- Wikimedia Commons
- PhysioNet

Each strip requires:
- High-quality image file
- Correct classification (mmvt or pmvt)
- 3-4 explanation bullets specific to that strip's distinguishing features

### Key Distinguishing Features to Cover

**MMVT indicators:**
- Uniform (monomorphic) QRS complexes
- Regular R-R intervals
- AV dissociation
- Capture/fusion beats
- Concordance in precordial leads

**PMVT indicators:**
- Varying QRS morphology beat-to-beat
- Changing QRS axis
- Irregular R-R intervals
- Torsades de Pointes: sinusoidal amplitude variation ("twisting of the points")
- No consistent bundle branch block pattern

## File Structure

```
EKG Website/
  index.html          # Everything: markup, styles, JS, card data
  images/
    mmvt-001.png
    mmvt-002.png
    ...
    pmvt-001.png
    pmvt-002.png
    ...
```

## Out of Scope

- User accounts or server-side storage
- Management algorithms or treatment pathways
- Feature annotation or clickable zones on strips
- Multi-step questions
- Audio or video content
