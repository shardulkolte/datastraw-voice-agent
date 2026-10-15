
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Reuse the exact same backend tools used by Gemini.
# These functions access your existing database and policy logic.
from backend.app.services.gemini_agent import (
    get_order_details,
    check_order_cancellation,
    get_order_shipping_policy,
    get_return_eligibility,
    get_damage_eligibility,
    get_cod_eligibility,
)


SYSTEM_PROMPT = """
You are Aria, a friendly and concise customer support specialist
for Aura Skincare, a fictional Indian skincare brand.

Your job is to help customers with orders, shipping, cancellations,
returns, damaged products, and Cash on Delivery (COD).

POLICIES:
- Free shipping applies to orders above Rs 499.
- Orders below Rs 499 have a Rs 50 shipping fee.
- The policy does not specify the fee for an order worth exactly Rs 499.
- Standard delivery takes 3-5 business days.
- Returns are accepted within 7 days of delivery only for unopened,
  unused products in their original packaging.
- Damaged or defective products must be reported within 48 hours
  of delivery, with photos, for replacement.
- Orders can be cancelled only while their status is Processing.
- Shipped and Out for Delivery orders cannot be cancelled.
  Customers may refuse delivery at the doorstep.
- COD is available for orders up to Rs 2500, payable by cash or UPI.

TOOL RULES:
- You have access to six backend tools. Use them when needed.
- For any order-specific question, use the relevant backend tool.
- Use get_order_details to verify an order ID before stating its details.
- Use check_order_cancellation before answering whether an order
  can be cancelled.
- Use get_order_shipping_policy for the shipping fee of an existing order.
- Use get_return_eligibility for return eligibility.
- Use get_damage_eligibility for damaged or defective product reports.
- Use get_cod_eligibility to check COD eligibility.
- Never invent order details, customer names, prices, tracking numbers,
  delivery dates, or tool results.
- Never treat the number inside an order ID as a monetary amount.
  For example, WORK-400 is an order ID, not an order worth Rs 400.
- Only interpret an amount as money when the customer explicitly
  expresses it as a price or monetary value.
- If a tool reports that an order was not found, say that you could
  not find that order. Do not make up its details.
- If a tool fails or returns an error, explain that you could not
  verify the information right now. Do not pretend the operation succeeded.
- Do not claim that an order was cancelled, returned, refunded, or
  replaced unless the backend actually confirms that action.
- Ask a short clarifying question when essential information is missing.
- If a question is unrelated to Aura Skincare, politely explain
  that you can help with Aura Skincare support.
- Speak naturally and concisely, as in a real customer conversation.
"""


# OpenRouter tool definitions use the OpenAI-compatible tool format.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": (
                "Look up an order by its exact order ID. "
                "Use this for order status, customer, product, value, "
                "courier, tracking, and delivery information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID, such as ORD-101.",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_order_cancellation",
            "description": (
                "Check whether a specific order can be cancelled "
                "according to its current status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to check.",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_shipping_policy",
            "description": (
                "Look up an existing order and determine the applicable "
                "shipping policy or fee using backend order data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The existing order ID.",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_return_eligibility",
            "description": (
                "Check return eligibility using days since delivery "
                "and the product's condition and packaging."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days_since_delivery": {
                        "type": "integer",
                        "description": "Number of days since delivery.",
                    },
                    "unopened": {
                        "type": "boolean",
                        "description": "Whether the product is unopened.",
                    },
                    "unused": {
                        "type": "boolean",
                        "description": "Whether the product is unused.",
                    },
                    "original_packaging": {
                        "type": "boolean",
                        "description": (
                            "Whether the product is in its original packaging."
                        ),
                    },
                },
                "required": [
                    "days_since_delivery",
                    "unopened",
                    "unused",
                    "original_packaging",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_damage_eligibility",
            "description": (
                "Check whether a damaged or defective product report "
                "meets the reporting time limit and photo requirement."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hours_since_delivery": {
                        "type": "integer",
                        "description": "Hours since the order was delivered.",
                    },
                    "photos_provided": {
                        "type": "boolean",
                        "description": (
                            "Whether the customer has provided damage photos."
                        ),
                    },
                },
                "required": [
                    "hours_since_delivery",
                    "photos_provided",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cod_eligibility",
            "description": (
                "Check whether an order amount qualifies for "
                "Cash on Delivery under Aura Skincare's policy."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_value": {
                        "type": "integer",
                        "description": "The order value in rupees.",
                    }
                },
                "required": ["order_value"],
                "additionalProperties": False,
            },
        },
    },
]


# Only these known backend functions can be executed.
AVAILABLE_TOOLS = {
    "get_order_details": get_order_details,
    "check_order_cancellation": check_order_cancellation,
    "get_order_shipping_policy": get_order_shipping_policy,
    "get_return_eligibility": get_return_eligibility,
    "get_damage_eligibility": get_damage_eligibility,
    "get_cod_eligibility": get_cod_eligibility,
}


def _send_openrouter_request(payload: dict) -> dict:
    """Send a request to OpenRouter, retrying one transient failure."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    request = Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "Aura Skincare Voice Agent",
        },
        method="POST",
    )

    for attempt in range(2):
        try:
            with urlopen(request, timeout=35) as response:
                result = json.loads(response.read().decode("utf-8"))

            if not isinstance(result, dict):
                raise RuntimeError("OpenRouter returned an invalid response.")

            return result

        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")

            # Retry one temporary server-side failure.
            if exc.code in (500, 502, 503, 504) and attempt == 0:
                time.sleep(1)
                continue

            raise RuntimeError(
                f"OpenRouter returned HTTP {exc.code}: {details[:500]}"
            ) from exc

        except (URLError, TimeoutError) as exc:
            if attempt == 0:
                time.sleep(1)
                continue

            raise RuntimeError(
                "OpenRouter could not be reached or timed out."
            ) from exc

    raise RuntimeError("OpenRouter request failed after retrying.")


def _execute_tool(tool_call: dict) -> dict:
    """Validate and execute one approved backend tool call."""

    function_data = tool_call.get("function", {})
    tool_name = function_data.get("name")
    raw_arguments = function_data.get("arguments", "{}")

    if tool_name not in AVAILABLE_TOOLS:
        return {
            "error": f"Unknown or unavailable tool: {tool_name}"
        }

    try:
        arguments = (
            json.loads(raw_arguments)
            if isinstance(raw_arguments, str)
            else raw_arguments
        )

        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a JSON object.")

        result = AVAILABLE_TOOLS[tool_name](**arguments)

        # Tool functions are expected to return structured data.
        if isinstance(result, dict):
            return result

        return {"result": result}

    except Exception as exc:
        # Return a tool error rather than inventing a successful result.
        print(f"Tool {tool_name} failed: {exc}")
        return {
            "error": (
                f"The backend tool {tool_name} could not verify "
                "the requested information."
            )
        }


def ask_openrouter(message: str) -> str:
    """Generate a reply with OpenRouter and execute requested backend tools."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    # Allow the model to request tools and then respond using their results.
    max_tool_rounds = 4

    for _ in range(max_tool_rounds + 1):
        payload = {
            "model": model,
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "temperature": 0.2,
            "max_tokens": 500,
        }

        result = _send_openrouter_request(payload)
        choices = result.get("choices", [])

        if not choices:
            raise RuntimeError("OpenRouter returned no response choices.")

        assistant_message = choices[0].get("message", {})
        tool_calls = assistant_message.get("tool_calls") or []

        # If there are no tool calls, this should be the final answer.
        if not tool_calls:
            content = assistant_message.get("content")

            if isinstance(content, str) and content.strip():
                return content.strip()

            raise RuntimeError(
                "OpenRouter returned an empty response. "
                "The selected model may not support the requested response."
            )

        # Preserve the assistant's tool-call request in the conversation.
        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.get("content"),
                "tool_calls": tool_calls,
            }
        )

        # Execute each requested function on our own backend.
        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id")

            if not tool_call_id:
                raise RuntimeError(
                    "OpenRouter returned a tool call without an ID."
                )

            tool_result = _execute_tool(tool_call)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                        default=str,
                    ),
                }
            )

    raise RuntimeError(
        "OpenRouter exceeded the maximum number of tool-call rounds."
    )
