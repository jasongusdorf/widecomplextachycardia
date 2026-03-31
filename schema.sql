-- schema.sql
DROP TABLE IF EXISTS attempts;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  username    TEXT NOT NULL UNIQUE COLLATE NOCASE,
  institution TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE attempts (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      INTEGER NOT NULL,
  card_id      TEXT NOT NULL,
  correct      INTEGER NOT NULL,
  attempted_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_attempts_user ON attempts(user_id);
CREATE INDEX idx_attempts_user_card_correct ON attempts(user_id, card_id, correct);
