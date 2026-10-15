export type Speaker = "Customer" | "Aria";

export interface ChatMessage {
  id: string;
  speaker: Speaker;
  text: string;
  timestamp: string;
}

export type AgentStatus =
  | "Ready"
  | "Listening"
  | "Thinking"
  | "Speaking"
  | "Error"
  | "Call ended";

export interface CallSummaryData {
  customer_intent: string;
  order_id: string | null;
  resolution_status: string;
  call_summary: string;
}

export interface ChatResponse {
  reply: string;
}
