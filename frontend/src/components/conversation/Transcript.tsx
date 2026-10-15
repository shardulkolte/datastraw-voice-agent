import { Empty } from "antd";
import type { ChatMessage } from "../../types/voice";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: ChatMessage[];
}

export default function Transcript({ messages }: Props) {
  return (
    <div className="transcript-list" aria-live="polite">
      {messages.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="Your conversation will appear here."
        />
      ) : (
        messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))
      )}
    </div>
  );
}
