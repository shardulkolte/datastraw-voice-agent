import { CopyOutlined } from "@ant-design/icons";
import { Button, Empty, message } from "antd";
import type { CallSummaryData } from "../../types/voice";

interface Props {
  summary: CallSummaryData | null;
}

export default function CallSummary({ summary }: Props) {
  const [messageApi, contextHolder] = message.useMessage();

  async function copySummary() {
    if (!summary) return;

    try {
      await navigator.clipboard.writeText(JSON.stringify(summary, null, 2));
      messageApi.success("JSON summary copied");
    } catch {
      messageApi.error("Couldn't copy the summary");
    }
  }

  return (
    <div>
      {contextHolder}

      {!summary ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="End the call to generate a summary."
        />
      ) : (
        <>
          <pre className="summary-json">{JSON.stringify(summary, null, 2)}</pre>
          <Button icon={<CopyOutlined />} block onClick={copySummary}>
            Copy JSON
          </Button>
        </>
      )}
    </div>
  );
}
