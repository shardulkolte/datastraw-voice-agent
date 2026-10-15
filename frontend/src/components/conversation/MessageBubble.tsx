import { Avatar, Card, Typography } from "antd";
import { CustomerServiceOutlined, UserOutlined } from "@ant-design/icons";
import type { ChatMessage } from "../../types/voice";

const { Paragraph, Text } = Typography;

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isAgent = message.speaker === "Aria";

  return (
    <div
      className={`message-row ${isAgent ? "message-agent" : "message-customer"}`}
    >
      <Avatar
        icon={isAgent ? <CustomerServiceOutlined /> : <UserOutlined />}
        className={isAgent ? "agent-avatar" : "customer-avatar"}
      />

      <Card size="small" className="message-card">
        <Text strong>{message.speaker}</Text>
        <Paragraph className="message-text">{message.text}</Paragraph>
        <Text type="secondary" className="message-time">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </Text>
      </Card>
    </div>
  );
}
