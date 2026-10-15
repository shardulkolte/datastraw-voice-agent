import type { ChatResponse } from "../types/voice";
import type { ConversationLanguage } from "../hooks/useVoiceAgent";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

export async function sendChatMessage(
  message: string,
  language: ConversationLanguage = "english",
): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 30_000);

  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, language }),
      signal: controller.signal,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data?.detail || `Support service returned ${response.status}.`);
    }

    if (typeof data?.reply !== "string") {
      throw new Error("The support service returned an invalid response.");
    }

    return { reply: data.reply };
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("The response took too long. Please try again.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}
