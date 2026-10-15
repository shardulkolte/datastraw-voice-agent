const DEFAULT_ORDER_PREFIX = import.meta.env.VITE_DEFAULT_ORDER_PREFIX || "ORD";

const SMALL_NUMBERS: Record<string, number> = {
  zero: 0,
  oh: 0,
  one: 1,
  two: 2,
  three: 3,
  four: 4,
  five: 5,
  six: 6,
  seven: 7,
  eight: 8,
  nine: 9,
  ten: 10,
  eleven: 11,
  twelve: 12,
  thirteen: 13,
  fourteen: 14,
  fifteen: 15,
  sixteen: 16,
  seventeen: 17,
  eighteen: 18,
  nineteen: 19,
  twenty: 20,
  thirty: 30,
  forty: 40,
  fifty: 50,
  sixty: 60,
  seventy: 70,
  eighty: 80,
  ninety: 90,
};

function spokenNumberToDigits(phrase: string): string | null {
  const words = phrase
    .toLowerCase()
    .replace(/-/g, " ")
    .split(/\s+/)
    .filter(Boolean);

  if (!words.length) return null;

  // Spoken digit-by-digit IDs, e.g. "one zero one".
  if (
    words.every(
      (word) =>
        word in SMALL_NUMBERS &&
        SMALL_NUMBERS[word] >= 0 &&
        SMALL_NUMBERS[word] <= 9,
    )
  ) {
    return words.map((word) => SMALL_NUMBERS[word]).join("");
  }

  let total = 0;
  let current = 0;

  for (const word of words) {
    if (word === "and") continue;

    if (word === "hundred") {
      current = Math.max(current, 1) * 100;
      continue;
    }

    if (word === "thousand") {
      total += Math.max(current, 1) * 1000;
      current = 0;
      continue;
    }

    const value = SMALL_NUMBERS[word];

    if (value === undefined) return null;

    current += value;
  }

  return String(total + current);
}

function normalizeExplicitIds(text: string): string {
  // Examples: "ORD 101", "ORD hyphen 101", "AB-1234".
  return text
    .replace(
      /\b([a-z]{2,12})\s*(?:hyphen|dash)?\s*[- ]\s*(\d{2,})\b/gi,
      (_, prefix: string, digits: string) =>
        `${prefix.toUpperCase()}-${digits}`,
    )
    .replace(
      /\b([a-z]{2,12})\s+(?:hyphen|dash)\s+(\d{2,})\b/gi,
      (_, prefix: string, digits: string) =>
        `${prefix.toUpperCase()}-${digits}`,
    )
    .replace(
      /\b([a-z]{2,12})\s+(\d{2,})\b/gi,
      (_, prefix: string, digits: string) =>
        `${prefix.toUpperCase()}-${digits}`,
    );
}

export function normalizeOrderReferences(input: string): string {
  let text = input
    .replace(/\bO\s*[- ]\s*R\s*[- ]\s*D\b/gi, "ORD")
    .replace(/\b([A-Z])\s*-\s*([A-Z])\s*-\s*([A-Z])\b/gi, "$1$2$3");

  // Convert spoken number words after an order-related phrase.
  text = text.replace(
    /\b(order|order number|order id|order number is)\s+((?:zero|oh|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|and)(?:[\s-]+(?:zero|oh|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|and))*)\b/gi,
    (fullMatch, label: string, spoken: string) => {
      const digits = spokenNumberToDigits(spoken);
      if (!digits) return fullMatch;

      return `${label} ${DEFAULT_ORDER_PREFIX}-${digits}`;
    },
  );

  // If the customer says "order 101", apply the configured default prefix.
  text = text.replace(
    /\b(order(?:\s+(?:number|id))?)\s+(\d{2,})\b/gi,
    (_, label: string, digits: string) =>
      `${label} ${DEFAULT_ORDER_PREFIX}-${digits}`,
  );

  return normalizeExplicitIds(text);
}
