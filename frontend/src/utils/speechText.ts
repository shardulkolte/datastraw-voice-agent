export function cleanSpeechText(text: string): string {
  return (
    text
      // Remove fenced code blocks and their contents.
      .replace(/```[\s\S]*?```/g, " ")
      // Convert Markdown links into their readable labels.
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      // Remove Markdown headings and blockquote markers.
      .replace(/^\s{0,3}#{1,6}\s+/gm, "")
      .replace(/^\s*>\s?/gm, "")
      // Remove bold and italic markers.
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/__(.*?)__/g, "$1")
      .replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "$1")
      .replace(/(?<!_)_([^_\n]+)_(?!_)/g, "$1")
      // Remove inline-code markers.
      .replace(/`([^`]+)`/g, "$1")
      // Turn Markdown bullets into natural pauses.
      .replace(/^\s*[-*+]\s+/gm, "")
      .replace(/^\s*\d+\.\s+/gm, "")
      // Remove leftover formatting symbols.
      .replace(/[*_`#>|]/g, "")
      // Normalize whitespace.
      .replace(/[ \t]+/g, " ")
      .replace(/\n{3,}/g, "\n\n")

      .trim()
  );
}
