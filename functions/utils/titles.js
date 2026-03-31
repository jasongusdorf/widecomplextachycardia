const THRESHOLDS = [
  { min: 300, title: 'EP Cardiologist' },
  { min: 250, title: 'General Cardiologist' },
  { min: 200, title: 'EP Fellow' },
  { min: 150, title: 'Cardiology Fellow' },
  { min: 110, title: 'SAR' },
  { min: 70,  title: 'JAR' },
  { min: 30,  title: 'Intern' },
  { min: 0,   title: 'Med Student' }
];

export function getTitle(uniqueCorrect) {
  for (const t of THRESHOLDS) {
    if (uniqueCorrect >= t.min) return t.title;
  }
  return 'Med Student';
}
