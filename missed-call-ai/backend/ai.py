"""
The AI side: builds the prompt, talks to Claude, and runs the job-capture tools.
"""

import os
from anthropic import Anthropic

from database import Business

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


TOOLS = [
    {
        "name": "submit_job",
        "description": (
            "Send a qualified job request to the business owner. Call this once you have the customer's "
            "name, service address, a description of the problem, and how urgent it is. Preferred time is "
            "optional. Only call it once per conversation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string"},
                "address": {"type": "string", "description": "Service address including city"},
                "issue": {"type": "string", "description": "Short description of the problem"},
                "urgency": {"type": "string", "enum": ["emergency", "soon", "flexible"]},
                "preferred_time": {"type": "string", "description": "When the customer would like a visit"},
            },
            "required": ["customer_name", "address", "issue", "urgency"],
        },
    },
    {
        "name": "hand_off_to_owner",
        "description": (
            "Ask the owner to personally follow up. Use when the customer asks for a human, is upset, asks "
            "something you can't answer (exact quotes, billing disputes, warranty claims), or is outside the "
            "service area."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    },
]


def build_system_prompt(business: Business) -> str:
    prompt = f"""You are the text-message assistant for {business.name}, a {business.trade} company in the Sacramento area.
A customer just called and nobody could pick up, so you're following up by text. Your job is to make sure this job is not lost.

## Goals, in order
1. Find out what they need help with.
2. If it sounds dangerous (gas smell, sparking, flooding, no heat/AC with elderly, infants or medical needs in extreme weather), tell them to call 911 or their utility first if there is any danger, and mark urgency "emergency".
3. Collect: name, service address, the problem, urgency, and a preferred time window.
4. Call submit_job, then tell them the owner will text or call to confirm a time.

## Rules
- This is SMS: keep every reply under 300 characters, plain text, no markdown, no emojis beyond one at most.
- Ask one or two questions at a time, never a long list.
- Never promise an exact price or exact arrival time. You can share ranges only if listed below.
- Never invent services, prices, or policies that aren't listed below.
- Be warm, quick, and local. Sound like a helpful office manager, not a robot.
- If they say they already got help or no longer need service, thank them and stop.

## Business info
- Service area: {business.service_area}
- Hours: {business.business_hours}
"""
    if business.custom_knowledge:
        prompt += f"\n## Services, pricing & policies\n{business.custom_knowledge}\n"
    return prompt


def first_text(business: Business) -> str:
    """The text a caller gets right after a missed call."""
    return (f"Hi, this is {business.name}. Sorry we missed your call! We're probably on a job. "
            f"What can we help you with? Reply here and we'll get you taken care of.")


def generate_reply(business: Business, history: list[dict], run_tool) -> str:
    """
    history: [{"role": "user"|"assistant", "content": str}, ...] ending with the customer's latest text.
    run_tool: callback(name, input) -> str result shown to the model.
    Returns the SMS text to send back.
    """
    client = get_client()
    messages = [dict(m) for m in history]
    system = build_system_prompt(business)

    for _ in range(3):  # at most a couple of tool rounds per inbound text
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            system=system,
            tools=TOOLS,
            messages=messages,
        )
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if response.stop_reason != "tool_use" or not tool_uses:
            text = "".join(b.text for b in response.content if b.type == "text").strip()
            return text or "Thanks! The owner will be in touch shortly."

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": t.id, "content": run_tool(t.name, t.input)}
                for t in tool_uses
            ],
        })

    return "Thanks! I've passed this along and the owner will reach out shortly."
