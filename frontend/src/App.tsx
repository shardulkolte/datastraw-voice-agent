import { useState } from "react";
import { Alert, Card, Col, Row, Select, Space, Typography } from "antd";
import AppHeader from "./components/layout/AppHeader";
import AppFooter from "./components/layout/AppFooter";
import VoiceControls from "./components/voice/VoiceControls";
import VoiceStatus from "./components/voice/VoiceStatus";
import Transcript from "./components/conversation/Transcript";
import SampleOrders from "./components/orders/SampleOrders";
import CallSummary from "./components/summary/CallSummary";
import { useVoiceAgent } from "./hooks/useVoiceAgent";
import type {
  ConversationLanguage,
  VoicePreference,
} from "./hooks/useVoiceAgent";
import "./App.css";

const { Title, Text } = Typography;

export default function App() {
  const [language, setLanguage] = useState<ConversationLanguage>("english");
  const [voicePreference, setVoicePreference] =
    useState<VoicePreference>("indian-hindi");

  const {
    messages,
    status,
    error,
    summary,
    isActive,
    startCall,
    endCall,
    resetCall,
  } = useVoiceAgent({ language, voicePreference });

  return (
    <div className="app-shell">
      <AppHeader />

      <main>
        <section className="hero-section">
          <Text className="eyebrow">AURA SKINCARE · CUSTOMER EXPERIENCE</Text>
          <Title level={1}>A little care goes a long way.</Title>
          <Text className="hero-description">
            Meet Aria, your virtual skincare support specialist. Ask about
            orders, delivery, returns, or payments.
          </Text>
        </section>

        <Row gutter={[20, 20]} align="top">
          <Col xs={24} lg={15}>
            <Card className="main-panel">
              <div className="panel-heading">
                <div>
                  <Title level={4}>Voice conversation</Title>
                  <Text type="secondary">
                    Speak naturally. Aria is ready to help.
                  </Text>
                </div>
                <VoiceStatus status={status} />
              </div>

              <Card size="small" className="language-panel">
                <Space wrap size="middle">
                  <div>
                    <Text strong>Conversation language</Text>
                    <Select
                      aria-label="Conversation language"
                      value={language}
                      disabled={isActive}
                      onChange={(value: ConversationLanguage) =>
                        setLanguage(value)
                      }
                      style={{ display: "block", minWidth: 180, marginTop: 6 }}
                      options={[
                        { value: "english", label: "English" },
                        { value: "hinglish", label: "Hinglish" },
                      ]}
                    />
                  </div>
                  <div>
                    <Text strong>Aria's voice</Text>
                    <Select
                      aria-label="Aria voice preference"
                      value={voicePreference}
                      disabled={isActive}
                      onChange={(value: VoicePreference) =>
                        setVoicePreference(value)
                      }
                      style={{ display: "block", minWidth: 220, marginTop: 6 }}
                      options={[
                        {
                          value: "indian-hindi",
                          label: "Indian Hindi (female preferred)",
                        },
                        {
                          value: "auto",
                          label: "Automatic (female preferred)",
                        },
                      ]}
                    />
                  </div>
                </Space>
                <Text
                  type="secondary"
                  style={{ display: "block", marginTop: 8 }}
                >
                  Choose English or Hinglish before starting. Aria prefers an
                  Indian Hindi female voice; available voices depend on your
                  browser and system.
                </Text>
              </Card>

              <div
                className={`voice-illustration ${status.toLowerCase().replace(" ", "-")}`}
              >
                <div className="voice-orb">
                  <span>✦</span>
                </div>
                <Title level={4}>
                  {status === "Listening"
                    ? "I'm listening"
                    : status === "Thinking"
                      ? "Let me check that"
                      : status === "Speaking"
                        ? "Aria is speaking"
                        : status === "Call ended"
                          ? "Call completed"
                          : "Hello, I'm Aria"}
                </Title>
                <Text type="secondary">
                  {isActive
                    ? "Ask a question about your Aura Skincare order."
                    : "Start a call to begin your conversation."}
                </Text>

                <div className="voice-buttons">
                  <VoiceControls
                    isActive={isActive}
                    onStart={startCall}
                    onEnd={endCall}
                    onReset={resetCall}
                  />
                </div>
                <Text type="secondary" className="microphone-note">
                  Your browser may ask for microphone permission.
                </Text>
              </div>

              {error && (
                <Alert
                  className="error-alert"
                  type="error"
                  showIcon
                  message="Voice support needs attention"
                  description={error}
                />
              )}

              <div className="section-heading">
                <Title level={5}>Conversation transcript</Title>
                <Text type="secondary">{messages.length} messages</Text>
              </div>

              <Transcript messages={messages} />
            </Card>
          </Col>

          <Col xs={24} lg={9}>
            <Space direction="vertical" size="large" className="side-panels">
              <Card title="Sample orders" className="side-panel">
                <Text type="secondary" className="panel-description">
                  Use these reference orders when testing Aria.
                </Text>
                <SampleOrders />
              </Card>

              <Card title="Post-call summary" className="side-panel">
                <Text type="secondary" className="panel-description">
                  Structured details from the conversation.
                </Text>
                <CallSummary summary={summary} />
              </Card>
            </Space>
          </Col>
        </Row>
      </main>

      <AppFooter />
    </div>
  );
}
