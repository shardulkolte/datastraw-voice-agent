import { Badge, Tag } from "antd";
import type { AgentStatus } from "../../types/voice";

interface Props {
  status: AgentStatus;
}

const statusColors: Record<AgentStatus, string> = {
  Ready: "default",
  Listening: "processing",
  Thinking: "warning",
  Speaking: "success",
  Error: "error",
  "Call ended": "default",
};

const badgeStatuses: Record<
  AgentStatus,
  "default" | "processing" | "success" | "warning" | "error"
> = {
  Ready: "default",
  Listening: "processing",
  Thinking: "warning",
  Speaking: "success",
  Error: "error",
  "Call ended": "default",
};

export default function VoiceStatus({ status }: Props) {
  return (
    <Tag color={statusColors[status]} className="voice-status">
      <Badge status={badgeStatuses[status]} />
      <span>{status}</span>
    </Tag>
  );
}
