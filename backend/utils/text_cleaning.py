import re


def clean_ai_output(text: str) -> str:
    """
    Strips internal thoughts, reasoning tags, and meta-monologue from LLM output.
    Handles:
    - <thought>...</thought> (case-insensitive, multiline)
    - <think>...</think>
    - <reasoning>...</reasoning>
    - Mismatched or unclosed tags
    - Explicit prefixes like 'Thinking Process:', 'Thought:', 'Reasoning:'
    """
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # 1. Closed reasoning tags (<thought>...</thought>, <think>...</think>, <reasoning>...</reasoning>)
    cleaned = re.sub(
        r"<(thought|think|reasoning)>.*?</\1>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # 2. Mismatched closing tags (<thought>...</think>, etc.)
    cleaned = re.sub(
        r"<(thought|think|reasoning)>.*?</(thought|think|reasoning)>",
        "",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # 3. Explicit 'Thinking Process:', 'Thought:', or 'Reasoning:' blocks
    cleaned = re.sub(
        r"^(?:Thought|Thinking Process|Reasoning):\s*[\s\S]*?(?=\n\s*\n|\Z)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # 4. Unclosed tag followed by paragraph breaks
    if re.search(r"<(thought|think|reasoning)>", cleaned, flags=re.IGNORECASE):
        parts = re.split(r"\n\s*\n", cleaned)
        cleaned_parts = [
            p for p in parts if not re.match(r"^\s*<(thought|think|reasoning)>", p, flags=re.IGNORECASE)
        ]
        cleaned = "\n\n".join(cleaned_parts)

    # 5. Any remaining standalone opening or closing tags
    cleaned = re.sub(
        r"</?(thought|think|reasoning)>",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    return cleaned.strip()
