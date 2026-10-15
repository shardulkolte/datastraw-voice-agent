import type { CallSummaryData, ChatMessage } from "../types/voice";
import { extractOrderIdFromText } from "./summaryOrder";

export function createCallSummary(messages: ChatMessage[]): CallSummaryData {
  const customerMessages = messages.filter(
    (message) => message.speaker === "Customer",
  );
  const agentMessages = messages.filter(
    (message) => message.speaker === "Aria",
  );

  const customerText = customerMessages.map((m) => m.text).join(" ");
  const agentText = agentMessages.map((m) => m.text).join(" ");

  let customerIntent = "GENERAL_SUPPORT";

  if (/cancel/i.test(customerText)) customerIntent = "ORDER_CANCELLATION";
  else if (/track|status|delivery|where.*order/i.test(customerText))
    customerIntent = "ORDER_TRACKING";
  else if (/return|refund/i.test(customerText))
    customerIntent = "RETURN_OR_REFUND";
  else if (/damage|defective|broken/i.test(customerText))
    customerIntent = "DAMAGED_PRODUCT";
  else if (/cod|cash on delivery|payment/i.test(customerText))
    customerIntent = "PAYMENT_ENQUIRY";

  let resolutionStatus = "INCOMPLETE";

  if (/couldn't find|could not find|no order was found/i.test(agentText)) {
    resolutionStatus = "ORDER_NOT_FOUND";
  } else if (agentMessages.length > 0) {
    resolutionStatus = "RESPONSE_PROVIDED";
  }

  return {
    customer_intent: customerIntent,
    order_id: extractOrderIdFromText(customerText),
    resolution_status: resolutionStatus,
    call_summary: messages
      .map((message) => `${message.speaker}: ${message.text}`)
      .join("\n"),
  };
}
