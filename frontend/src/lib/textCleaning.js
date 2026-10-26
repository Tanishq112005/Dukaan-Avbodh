/**
 * Utility to strip internal reasoning, thought tags, and meta-monologue from AI outputs.
 * Ensures mobile and desktop chat users only see polished, user-facing responses.
 */
export function cleanAiText(rawText, isStreaming = false) {
  if (!rawText || typeof rawText !== "string") return "";

  let text = rawText.replace(/\r\n/g, "\n").replace(/\r/g, "\n");

  // 1. Detect and parse raw JSON responses (e.g. ```json { "message": "..." } ``` or raw `{ "message": "..." }`)
  const jsonBlockMatch = text.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
  if (jsonBlockMatch) {
    try {
      const parsed = JSON.parse(jsonBlockMatch[1]);
      if (parsed.message) text = parsed.message;
    } catch {}
  } else if (text.trim().startsWith("{") && text.trim().endsWith("}")) {
    try {
      const parsed = JSON.parse(text.trim());
      if (parsed.message) text = parsed.message;
    } catch {}
  }

  // 2. Strip closed reasoning tags (<think>...</think>, <thought>...</thought>, <reasoning>...</reasoning>)
  text = text.replace(/<(?:think|thought|reasoning)>[\s\S]*?<\/(?:think|thought|reasoning)>/gi, "");

  // 3. During streaming, if an opening tag exists without a closing tag,
  // strip everything from the tag onwards so internal thinking does not leak into the UI
  if (isStreaming) {
    text = text.replace(/<(?:think|thought|reasoning)>[\s\S]*$/gi, "");
  }

  // 4. Strip any residual opening or closing tags
  text = text.replace(/<\/?(?:think|thought|reasoning|system)>/gi, "");

  // 5. Strip explicit 'Thinking Process:', 'Thought:', 'Reasoning:' blocks
  text = text.replace(/^(?:Thought|Thinking Process|Reasoning):\s*[\s\S]*?(?=\n\s*\n|\Z)/gim, "");

  // 6. Strip system / role prefixes (e.g. 'Assistant:', 'System:', 'Human:')
  text = text.replace(/^(?:Assistant|System|Human):\s*/gim, "");

  // 7. Strip trailing internal markers or metadata artifacts
  text = text.replace(/\[\s*DONE\s*\]/gi, "");

  return text.trim();
}
