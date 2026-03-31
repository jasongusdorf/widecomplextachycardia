// functions/api/leaderboard.js

import { getTitle } from '../utils/titles.js';

export async function onRequestGet(context) {
  const { env } = context;

  const rows = await env.DB.prepare(`
    SELECT
      u.id,
      u.username,
      u.institution,
      COUNT(DISTINCT CASE WHEN a.correct = 1 THEN a.card_id END) AS unique_correct,
      COUNT(*) AS total_attempted,
      ROUND(CAST(SUM(a.correct) AS REAL) / COUNT(*) * 100, 1) AS accuracy
    FROM users u
    JOIN attempts a ON a.user_id = u.id
    GROUP BY u.id
    ORDER BY unique_correct DESC, accuracy DESC
    LIMIT 100
  `).all();

  const leaderboard = rows.results.map(function(row, i) {
    return {
      rank: i + 1,
      username: row.username,
      institution: row.institution,
      uniqueCorrect: row.unique_correct,
      accuracy: row.accuracy,
      title: getTitle(row.unique_correct)
    };
  });

  return Response.json(leaderboard);
}
