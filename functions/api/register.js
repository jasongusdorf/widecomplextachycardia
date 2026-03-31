// functions/api/register.js

import { containsProfanity } from '../utils/profanity.js';

export async function onRequestPost(context) {
  const { request, env } = context;
  const body = await request.json();
  const username = (body.username || '').trim();
  const institution = (body.institution || '').trim();

  // Validate username length
  if (username.length < 3 || username.length > 20) {
    return Response.json(
      { error: 'Username must be 3-20 characters' },
      { status: 400 }
    );
  }

  // Validate username characters (alphanumeric + underscores)
  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    return Response.json(
      { error: 'Username can only contain letters, numbers, and underscores' },
      { status: 400 }
    );
  }

  // Validate institution
  if (institution.length === 0) {
    return Response.json(
      { error: 'Institution is required' },
      { status: 400 }
    );
  }

  // Profanity check
  if (containsProfanity(username) || containsProfanity(institution)) {
    return Response.json(
      { error: 'Username or institution contains inappropriate language' },
      { status: 400 }
    );
  }

  // Check uniqueness (COLLATE NOCASE handles case-insensitive)
  const existing = await env.DB.prepare(
    'SELECT id FROM users WHERE username = ?'
  ).bind(username).first();

  if (existing) {
    return Response.json(
      { error: 'Username is already taken' },
      { status: 409 }
    );
  }

  // Insert user
  const result = await env.DB.prepare(
    'INSERT INTO users (username, institution) VALUES (?, ?)'
  ).bind(username, institution).run();

  return Response.json({
    id: result.meta.last_row_id,
    username: username,
    institution: institution
  }, { status: 201 });
}
