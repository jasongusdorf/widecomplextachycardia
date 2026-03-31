// functions/api/answer.js

import { getTitle } from '../utils/titles.js';

export async function onRequestPost(context) {
  const { request, env } = context;
  const body = await request.json();
  const userId = body.userId;
  const cardId = (body.cardId || '').trim();
  const correct = body.correct ? 1 : 0;

  if (!userId || !cardId) {
    return Response.json(
      { error: 'userId and cardId are required' },
      { status: 400 }
    );
  }

  // Verify user exists
  const user = await env.DB.prepare(
    'SELECT id FROM users WHERE id = ?'
  ).bind(userId).first();

  if (!user) {
    return Response.json(
      { error: 'User not found' },
      { status: 404 }
    );
  }

  // Insert attempt
  await env.DB.prepare(
    'INSERT INTO attempts (user_id, card_id, correct) VALUES (?, ?, ?)'
  ).bind(userId, cardId, correct).run();

  // Compute updated stats
  const stats = await env.DB.prepare(`
    SELECT
      COUNT(DISTINCT CASE WHEN correct = 1 THEN card_id END) AS unique_correct,
      COUNT(*) AS total_attempted,
      ROUND(CAST(SUM(correct) AS REAL) / COUNT(*) * 100, 1) AS accuracy
    FROM attempts
    WHERE user_id = ?
  `).bind(userId).first();

  return Response.json({
    uniqueCorrect: stats.unique_correct,
    totalAttempted: stats.total_attempted,
    accuracy: stats.accuracy,
    title: getTitle(stats.unique_correct)
  });
}
