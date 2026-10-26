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

    return cleaned.strip()


class StreamingThoughtFilter:
    """
    Online streaming buffer that detects and filters out internal model thoughts/reasoning:
    - <thought> ... </thought>
    - <think> ... </think>
    - <reasoning> ... </reasoning>
    as tokens are streamed chunk-by-chunk in real time.
    Emits only clean, user-facing text tokens with zero thought leakage.
    """

    def __init__(self):
        self.in_thought = False
        self.buffer = ""
        self.open_tags = ["<thought>", "<think>", "<reasoning>"]
        self.close_tags = ["</thought>", "</think>", "</reasoning>"]
        self.max_tag_len = max(len(t) for t in self.open_tags + self.close_tags)

    def process(self, chunk: str) -> str:
        self.buffer += chunk
        output = []

        while self.buffer:
            if not self.in_thought:
                # Look for start of any open tag
                found_open = None
                earliest_pos = -1
                for tag in self.open_tags:
                    pos = self.buffer.lower().find(tag)
                    if pos != -1 and (earliest_pos == -1 or pos < earliest_pos):
                        earliest_pos = pos
                        found_open = tag

                if found_open is not None:
                    # Emit everything before open tag
                    if earliest_pos > 0:
                        output.append(self.buffer[:earliest_pos])
                    self.buffer = self.buffer[earliest_pos + len(found_open):]
                    self.in_thought = True
                else:
                    # Check for partial open tag at the end (e.g. '<th')
                    partial_match = False
                    for tag in self.open_tags:
                        for l in range(1, len(tag)):
                            if self.buffer.lower().endswith(tag[:l]):
                                safe_len = len(self.buffer) - l
                                if safe_len > 0:
                                    output.append(self.buffer[:safe_len])
                                    self.buffer = self.buffer[safe_len:]
                                partial_match = True
                                break
                        if partial_match:
                            break
                    if not partial_match:
                        output.append(self.buffer)
                        self.buffer = ""
                    break
            else:
                # Inside thought: look for close tag
                found_close = None
                earliest_pos = -1
                for tag in self.close_tags:
                    pos = self.buffer.lower().find(tag)
                    if pos != -1 and (earliest_pos == -1 or pos < earliest_pos):
                        earliest_pos = pos
                        found_close = tag

                if found_close is not None:
                    # Discard thought content, resume normal text
                    self.buffer = self.buffer[earliest_pos + len(found_close):]
                    self.in_thought = False
                else:
                    # Keep only last possible partial close tag
                    keep_len = self.max_tag_len
                    if len(self.buffer) > keep_len:
                        self.buffer = self.buffer[-keep_len:]
                    break

        return "".join(output)

    def flush(self) -> str:
        if not self.in_thought and self.buffer:
            res = self.buffer
            self.buffer = ""
            return res
        self.buffer = ""
        return ""
