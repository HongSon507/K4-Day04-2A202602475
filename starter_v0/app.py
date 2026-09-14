from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import run_model_tool_loop, trim_history
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def save_transcript(
    *,
    provider_name: str,
    model: str | None,
    version_data: dict[str, str],
    system_prompt_path: Path,
    tools_path: Path,
    turns: list[dict[str, Any]],
) -> Path:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    if "transcript_id" not in st.session_state:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        st.session_state.transcript_id = f"ui_{version_data['version']}_{provider_name}_{timestamp}"
    path = TRANSCRIPTS_DIR / f"{st.session_state.transcript_id}.transcript.json"
    payload = {
        "transcript_id": st.session_state.transcript_id,
        **version_data,
        "provider": provider_name,
        "model": model,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "created_at": st.session_state.get("transcript_created_at", now_iso()),
        "updated_at": now_iso(),
        "turns": turns,
    }
    path.write_text(json_text(payload), encoding="utf-8")
    return path


def render_tool_event(event: dict[str, Any], index: int) -> None:
    tool_name = event.get("tool", "unknown_tool")
    result = event.get("result", event.get("error"))
    with st.expander(f"{index}. {tool_name}", expanded=True):
        st.caption("Arguments")
        st.code(json_text(event.get("args", {})), language="json")
        st.caption("Result / error")
        st.code(json_text(result), language="json")


def render_turn(turn: dict[str, Any], index: int) -> None:
    status = turn.get("status", "unknown")
    st.markdown(f"### Turn {index}: `{status}`")
    st.markdown(f"**User request**  \n{turn.get('user', '')}")
    st.markdown(f"**Final response**  \n{turn.get('assistant_text') or 'No response'}")
    rounds = turn.get("rounds", [])
    st.caption(f"Rounds: {len(rounds)} | Tool events: {len(turn.get('tool_events', []))}")
    for round_record in rounds:
        with st.expander(f"Round {round_record.get('round')}", expanded=True):
            if round_record.get("assistant_text"):
                st.write(round_record["assistant_text"])
            calls = round_record.get("tool_calls", [])
            if calls:
                st.caption("Tool calls")
                st.code(json_text(calls), language="json")
            for event_index, event in enumerate(round_record.get("tool_results", []), start=1):
                render_tool_event(event, event_index)


def main() -> None:
    st.set_page_config(page_title="Helpdesk Trace Lab", page_icon="+", layout="wide")
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
        html, body, [class*='css'] { font-family: 'Space Grotesk', sans-serif; }
        code, pre { font-family: 'DM Mono', monospace !important; }
        .hero { padding: 1rem 0 1.5rem; border-bottom: 1px solid #d8d4ca; margin-bottom: 1.2rem; }
        .eyebrow { color: #b34d2e; font: 500 0.75rem 'DM Mono'; letter-spacing: .08em; text-transform: uppercase; }
        .hero h1 { font-size: clamp(2rem, 5vw, 4.8rem); line-height: .95; margin: .45rem 0; color: #182522; }
        .hero p { max-width: 680px; color: #5a625d; font-size: 1.05rem; }
        .evidence-strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem; margin: 1.25rem 0 .5rem; }
        .evidence-item { background: #17332d; border-top: 3px solid #e17a4f; padding: .85rem 1rem; min-width: 0; }
        .evidence-label { color: #b9d2c7; font: 500 .7rem 'DM Mono'; letter-spacing: .08em; text-transform: uppercase; }
        .evidence-value { color: #fff8e9; display: block; font: 500 .9rem 'DM Mono'; margin-top: .45rem; overflow-wrap: anywhere; }
        .transcript-path { color: #69726c; font: .78rem 'DM Mono'; margin: .4rem 0 1.5rem; overflow-wrap: anywhere; }
        @media (max-width: 700px) { .evidence-strip { grid-template-columns: 1fr; } }
        </style>
        <div class="hero">
          <div class="eyebrow">IT Helpdesk / trace console</div>
          <h1>Ask clearly.<br>Audit everything.</h1>
          <p>A live view of the shared model tool loop, its decisions, and the evidence written to disk.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Run controls")
        provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"])
        version_label = st.text_input("Artifact version", value="v0")
        model = st.text_input("Model override", value="", help="Leave blank to use the provider default.") or None
        history_window = st.slider("History window", min_value=0, max_value=10, value=5)
        max_tool_rounds = st.slider("Max tool rounds", min_value=1, max_value=10, value=4)
        if st.button("New transcript", use_container_width=True):
            for key in ["turns", "history", "transcript_id", "transcript_created_at"]:
                st.session_state.pop(key, None)
            st.rerun()

    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    version_data = artifact_version_dict(build_artifact_version(version_label, system_prompt_path, tools_path))
    st.session_state.setdefault("turns", [])
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("transcript_created_at", now_iso())

    st.markdown(
        f"""
        <div class="evidence-strip" aria-label="Artifact evidence">
          <div class="evidence-item"><span class="evidence-label">Artifact version</span><span class="evidence-value">{version_data['artifact_version']}</span></div>
          <div class="evidence-item"><span class="evidence-label">Prompt SHA-256</span><span class="evidence-value">{version_data['prompt_hash'][:12]}...</span></div>
          <div class="evidence-item"><span class="evidence-label">Tools SHA-256</span><span class="evidence-value">{version_data['tools_hash'][:12]}...</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    transcript_path = TRANSCRIPTS_DIR / f"{st.session_state.get('transcript_id', 'pending')}.transcript.json"
    transcript_label = transcript_path.name if "transcript_id" in st.session_state else "created on first run"
    st.markdown(f"<div class=\"transcript-path\">Transcript: {transcript_label}</div>", unsafe_allow_html=True)

    st.subheader("Live request")
    user_text = st.chat_input("Describe the helpdesk issue...")
    if user_text:
        try:
            system_prompt = system_prompt_path.read_text(encoding="utf-8")
            declarations = load_tool_declarations(tools_path)
            provider = make_provider(provider_name)
            selected_model = model or getattr(provider, "default_model", None)
            messages = [
                {"role": "system", "content": system_prompt},
                *trim_history(st.session_state.history, history_window),
                {"role": "user", "content": user_text},
            ]
            with st.status("Running model tool loop...", expanded=True) as status:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=to_openai_tools(declarations),
                    model=model,
                    max_tool_rounds=max_tool_rounds,
                )
                status.update(label=f"Completed: {result['status']}", state="complete")
            turn = {
                "turn_index": len(st.session_state.turns) + 1,
                "started_at": now_iso(),
                "ended_at": now_iso(),
                "user": user_text,
                **result,
            }
            st.session_state.turns.append(turn)
            st.session_state.history.extend([
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": result.get("assistant_text", "")},
            ])
            path = save_transcript(
                provider_name=provider_name,
                model=selected_model,
                version_data=version_data,
                system_prompt_path=system_prompt_path,
                tools_path=tools_path,
                turns=st.session_state.turns,
            )
            st.success(f"Transcript saved: {path}")
        except Exception as exc:
            st.error(f"{type(exc).__name__}: {exc}")

    if not st.session_state.turns:
        st.info("Submit a request to see the assistant response and every tool trace here.")
    else:
        st.subheader("Trace")
        for index, turn in enumerate(reversed(st.session_state.turns), start=1):
            render_turn(turn, len(st.session_state.turns) - index + 1)


if __name__ == "__main__":
    main()