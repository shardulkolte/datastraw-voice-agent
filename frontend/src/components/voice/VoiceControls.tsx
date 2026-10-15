import { AudioOutlined, PhoneOutlined, StopOutlined } from "@ant-design/icons";
import { Button, Space } from "antd";

interface Props {
  isActive: boolean;
  onStart: () => void;
  onEnd: () => void;
  onReset: () => void;
}

export default function VoiceControls({
  isActive,
  onStart,
  onEnd,
  onReset,
}: Props) {
  return (
    <Space wrap size="middle">
      <Button
        type="primary"
        size="large"
        icon={<AudioOutlined />}
        onClick={onStart}
        disabled={isActive}
      >
        Start Call
      </Button>

      <Button
        danger
        size="large"
        icon={<PhoneOutlined />}
        onClick={onEnd}
        disabled={!isActive}
      >
        End Call
      </Button>

      <Button size="large" icon={<StopOutlined />} onClick={onReset}>
        New Conversation
      </Button>
    </Space>
  );
}
