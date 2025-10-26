"""Chat function module
=========================

This module provides a single public function :func:`get_ai_response` that
communicates with OpenAI's chat completion API.  It maintains a conversation
history so that each request can be answered in context, handles basic error
scenarios, and allows a small amount of configuration (model, temperature,
system prompt, etc.).

The implementation follows the natural‑language specification found in
``chat_func.npy``.  All helper logic is kept inline – no additional files are
created – and external dependencies are imported as if they exist.
"""

from __future__ import annotations

import os
import logging
from typing import List, Dict, Tuple, Optional

# External dependency – assumed to be installed in the execution environment.
# The OpenAI Python SDK provides ``openai.ChatCompletion.create``.
import openai

# Configure a very small logger for optional debugging.
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_api_key() -> str:
    """Retrieve the OpenAI API key from the environment.

    Raises a ``RuntimeError`` with a clear message if the key is missing.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OpenAI API key not found. Set the 'OPENAI_API_KEY' environment variable."
        )
    return api_key


def _initial_system_message(system_prompt: Optional[str]) -> Dict[str, str]:
    """Create the initial system message if a custom prompt is supplied.

    Returns an empty dict when ``system_prompt`` is ``None``.
    """
    if system_prompt:
        return {"role": "system", "content": system_prompt}
    return {}


def _ensure_history(
    history: Optional[List[Dict[str, str]]], system_prompt: Optional[str]
) -> List[Dict[str, str]]:
    """Return a mutable conversation history.

    * If ``history`` is ``None`` a new list is created.
    * If the history is empty and a ``system_prompt`` is provided, the system
      message is inserted as the first entry.
    """
    hist = list(history) if history else []
    if not hist and system_prompt:
        sys_msg = _initial_system_message(system_prompt)
        if sys_msg:
            hist.append(sys_msg)
    return hist


def _call_openai(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """Invoke the OpenAI chat completion endpoint.

    Errors from the SDK are caught and re‑raised as ``RuntimeError`` with a
    concise description, satisfying graceful error handling.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message["content"].strip()
    except Exception as exc:  # Broad catch to cover auth, network, etc.
        logger.error("OpenAI request failed: %s", exc)
        raise RuntimeError(f"Failed to get response from OpenAI: {exc}") from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_ai_response(
    user_input: str,
    *,
    history: Optional[List[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 150,
) -> Tuple[str, List[Dict[str, str]]]:
    """Generate a concise AI response for *user_input*.

    Parameters
    ----------
    user_input:
        The transcribed speech or text from the user.
    history:
        Existing conversation history in the OpenAI message format.  If ``None``
        a new history list is created.
    system_prompt:
        Optional system‑level instruction that shapes the assistant's persona.
    model:
        The OpenAI model to use.  Defaults to a lightweight, fast model.
    temperature:
        Controls randomness; lower values make the output more deterministic.
    max_tokens:
        Upper bound on the number of tokens in the assistant's reply.

    Returns
    -------
    Tuple[str, List[Dict[str, str]]]
        ``(assistant_reply, updated_history)`` where ``updated_history``
        includes the new user message and the assistant's response.
    """
    # Validate API key early for a clear error message.
    _load_api_key()

    # Prepare conversation history.
    conv = _ensure_history(history, system_prompt)

    # Append the user's message.
    conv.append({"role": "user", "content": user_input or ""})

    if not user_input.strip():
        # Empty input – return empty response but keep history.
        return "", conv

    # Call the OpenAI API.
    assistant_reply = _call_openai(
        messages=conv,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Append assistant's reply to history.
    conv.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply, conv


# ---------------------------------------------------------------------------
# Simple interactive demo (runs when the module is executed directly)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    hist: List[Dict[str, str]] = []
    while True:
        try:
            user_msg = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if user_msg.lower() in {"exit", "quit"}:
            break
        reply, hist = get_ai_response(
            user_msg,
            history=hist,
            system_prompt="You are a helpful, concise assistant.",
        )
        print(f"AI: {reply}\n")
