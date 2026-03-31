// functions/api/user/[id].js

import { getTitle } from '../../utils/titles.js';

export async function onRequestGet(context) {
  const { env, params } = context;
  const userId = parseInt(params.id, 10);

  if (isNaN(userId)) {
    return Response.json({ error: 'Invalid user ID' }, { status: 400 });
  }

  const user = await env.DB.prepare(
    'SELECT id, username, institution FROM users WHERE id = ?'
  ).bind(userId).first();

  if (!user) {
    return Response.json({ error: 'User not found' }, { status: 404 });
  }

  // Get this user's stats
  const stats = await env.DB.prepare(`
    SELECT
      COUNT(DISTINCT CASE WHEN correct = 1 THEN card_id END) AS unique_correct,
      COUNT(*) AS total_attempted,
      ROUND(CAST(SUM(correct) AS REAL) / COUNT(*) * 100, 1) AS accuracy
    FROM attempts
    WHERE user_id = ?
  `).bind(userId).first();

  // Get this user's rank
  const rankResult = await env.DB.prepare(`
    SELECT COUNT(*) + 1 AS rank
    FROM (
      SELECT user_id,
        COUNT(DISTINCT CASE WHEN correct = 1 THEN card_id END) AS uc
      FROM attempts
      GROUP BY user_id
      HAVING uc > ?
    )
  `).bind(stats.unique_correct || 0).first();

  return Response.json({
    id: user.id,
    username: user.username,
    institution: user.institution,
    uniqueCorrect: stats.unique_correct || 0,
    totalAttempted: stats.total_attempted || 0,
    accuracy: stats.accuracy || 0,
    title: getTitle(stats.unique_correct || 0),
    rank: rankResult.rank
  });
}
