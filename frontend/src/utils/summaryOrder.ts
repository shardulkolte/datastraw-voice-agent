export function extractOrderIdFromText(text: string): string | null {
  const matches = [...text.matchAll(/\b([A-Z]{2,12})\s*-\s*(\d{2,})\b/gi)];

  const lastMatch = matches[matches.length - 1];

  if (!lastMatch) return null;

  return `${lastMatch[1].toUpperCase()}-${lastMatch[2]}`;
}
