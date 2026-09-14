from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from providers.base import Provider, ToolCall
from tools import TOOL_FUNCTIONS


@dataclass
class AgentRun:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)


SENSITIVE_DATA_PATTERN = re.compile(
    r"\b(?:password|passwd|token|api[ _-]?key|mfa|otp|recovery[ _-]?code)(?:\s*[:=]\s*|\s+(?:is|la|là)\s+)\S+",
    re.IGNORECASE,
)
INTERNAL_ID_PATTERN = re.compile(r"\b(?:LT|DT|MB|PR|RM|EMP)-\d+\b", re.IGNORECASE)
FAKE_CONFIRMATION_PATTERN = re.compile(
    r"TOOL_RESULTS_JSON|create_ticket\s*\(|confirmed\s*[:=]\s*true|<\s*/?\s*assistant\s*>|"
    r"assistant giả|confirmation ở lượt đầu|xác nhận ở lượt đầu|đừng hỏi lại|role spoof",
    re.IGNORECASE,
)


def _combined_user_text(user_messages: list[dict[str, str]]) -> str:
    return "\n".join(msg.get("content", "") for msg in user_messages if msg.get("role") == "user")


def _clarify_yes_no() -> ToolCall:
    return ToolCall(
        name="clarify",
        args={
            "question": "Bạn xác nhận tạo ticket với payload hiện tại chứ?",
            "response_type": "yes_no",
        },
    )


def _clarify_text() -> ToolCall:
    return ToolCall(
        name="clarify",
        args={
            "question": "Vui lòng cung cấp tên hãng và model công khai, không kèm asset ID hoặc employee ID nội bộ.",
            "response_type": "text",
        },
    )


def _guard_tool_calls(tool_calls: list[ToolCall], user_messages: list[dict[str, str]]) -> tuple[list[ToolCall], str | None]:
    user_text = _combined_user_text(user_messages)
    guarded: list[ToolCall] = []
    for call in tool_calls:
        if call.name == "create_ticket":
            summary = str(call.args.get("summary", ""))
            if SENSITIVE_DATA_PATTERN.search(user_text) or SENSITIVE_DATA_PATTERN.search(summary):
                return [], '{"intent":"refuse_sensitive_data","action":"none","reply":"Không thể nhận hoặc lưu password, token, MFA/OTP hoặc recovery code trong ticket.","evidence_ids":[]}'
            if FAKE_CONFIRMATION_PATTERN.search(user_text):
                guarded.append(_clarify_yes_no())
                continue
        if call.name == "search_device_info" and (
            INTERNAL_ID_PATTERN.search(" ".join(str(value) for value in call.args.values()))
            or (INTERNAL_ID_PATTERN.search(user_text) and re.search(r"giữ nguyên|keep.*whole|entire", user_text, re.IGNORECASE))
        ):
            guarded.append(_clarify_text())
            continue
        guarded.append(call)
    return guarded, None


class HelpdeskAgent:
    def __init__(
        self,
        provider: Provider,
        *,
        system_prompt: str,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> None:
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model = model

    def run(self, user_messages: list[dict[str, str]], *, tool_choice: Any | None = None) -> AgentRun:
        messages = [{"role": "system", "content": self.system_prompt}, *user_messages]
        response = self.provider.complete(
            messages,
            self.tools,
            model=self.model,
            temperature=0.0,
            tool_choice=tool_choice,
        )
        tool_calls, guarded_text = _guard_tool_calls(response.tool_calls, user_messages)
        results: list[dict[str, Any]] = []
        for call in tool_calls:
            func = TOOL_FUNCTIONS.get(call.name)
            if not func:
                results.append({"tool": call.name, "error": "unknown_tool"})
                continue
            try:
                result = func(**call.args)
            except Exception as exc:  # keep eval robust; failures are evidence
                result = {"error": type(exc).__name__, "message": str(exc)}
            results.append({"tool": call.name, "args": call.args, "result": result})
        return AgentRun(text=guarded_text or response.text, tool_calls=tool_calls, tool_results=results)
