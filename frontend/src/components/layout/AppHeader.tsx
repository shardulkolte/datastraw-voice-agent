import { CustomerServiceOutlined } from "@ant-design/icons";
import { Tag } from "antd";

export default function AppHeader() {
  return (
    <header className="app-header">
      <div className="brand">
        <div className="brand-icon">
          <CustomerServiceOutlined />
        </div>
        <div>
          <h1>Aura Skincare</h1>
          <p>Personal care, human connection</p>
        </div>
      </div>

      <Tag color="green" className="agent-tag">
        Aria · AI Support
      </Tag>
    </header>
  );
}
