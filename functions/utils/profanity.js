const BLOCKED_WORDS = [
  'ass', 'asshole', 'bastard', 'bitch', 'cock', 'cunt', 'damn', 'dick',
  'fuck', 'motherfucker', 'nigger', 'nigga', 'piss', 'pussy', 'shit',
  'slut', 'tits', 'whore', 'wanker', 'twat', 'fag', 'faggot', 'retard',
  'penis', 'vagina', 'dildo', 'anal', 'anus', 'ballsack', 'blowjob',
  'bollock', 'boner', 'boob', 'buttplug', 'clitoris', 'coon', 'cum',
  'deepthroat', 'ejaculate', 'felch', 'fellatio', 'fleshlight', 'gangbang',
  'handjob', 'hentai', 'jizz', 'kike', 'masturbat', 'nazi', 'nutsack',
  'orgasm', 'pedophil', 'porno', 'queef', 'scrotum', 'semen', 'sexist',
  'smegma', 'spic', 'testicle', 'viagra', 'vulva', 'wetback'
];

export function containsProfanity(text) {
  const lower = text.toLowerCase();
  return BLOCKED_WORDS.some(function(word) {
    return lower.includes(word);
  });
}
