import React from 'react';
import { cleanAiText } from '../../lib/textCleaning';

const URL_SPLIT = /(\*\*.*?\*\*|\[.*?\]\(https?:\/\/[^\s)]+\)|https?:\/\/[^\s<>"')\]]+)/g;
const PAYMENT_PATTERN = /razorpay|rzp\.io|rzp_/i;

function Linkish({ href, children, className }) {
  const isPayment = PAYMENT_PATTERN.test(href);
  const isInternal = href.startsWith('/') || href.startsWith('#');
  const target = isPayment || isInternal ? "_self" : "_blank";

  return (
    <a
      href={href}
      target={target}
      rel={target === "_blank" ? "noopener noreferrer" : undefined}
      className={className || "text-[#C45C26] hover:text-[#a3481b] underline underline-offset-2 font-semibold break-all"}
    >
      {children}
    </a>
  );
}

function parseInline(content, paymentUrl, state) {
  if (!content) return [];
  const parts = content.split(URL_SPLIT);

  return parts
    .map((part, j) => {
      if (!part) return null;

      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={j} className="font-bold text-inherit">
            {part.slice(2, -2)}
          </strong>
        );
      }

      const md = part.match(/^\[(.*?)\]\((https?:\/\/[^\s)]+)\)$/);
      const url = md ? md[2] : (/^https?:\/\//.test(part) ? part : null);

      if (url) {
        const isPayment = PAYMENT_PATTERN.test(url) || url === paymentUrl;
        if (isPayment) {
          if (state.seenPaymentLink) return null;
          state.seenPaymentLink = true;
          return null;
        }
        const label = md ? md[1] : url;
        return (
          <Linkish key={j} href={url}>
            {label}
          </Linkish>
        );
      }

      return <span key={j}>{part}</span>;
    })
    .filter(Boolean);
}

function parseBlocks(rawText, paymentUrl) {
  if (!rawText || typeof rawText !== 'string') return [];

  // Normalize line endings
  const normalized = rawText.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  const rawLines = normalized.split('\n');

  const blocks = [];
  let currentList = null; // { type: 'bullet' | 'numbered', items: [] }
  let currentParagraphLines = [];
  const state = { seenPaymentLink: false };

  const flushParagraph = () => {
    if (currentParagraphLines.length > 0) {
      const lines = currentParagraphLines
        .map((l) => l.trim())
        .filter(Boolean);
      if (lines.length > 0) {
        blocks.push({
          type: 'paragraph',
          lines: lines.map((line) => parseInline(line, paymentUrl, state)),
        });
      }
      currentParagraphLines = [];
    }
  };

  const flushList = () => {
    if (currentList && currentList.items.length > 0) {
      blocks.push(currentList);
      currentList = null;
    }
  };

  for (let i = 0; i < rawLines.length; i++) {
    const line = rawLines[i];
    const trimmed = line.trim();

    // Check if line is empty
    if (!trimmed) {
      flushParagraph();
      // Lookahead: In standard markdown loose lists, empty lines between items
      // do not break the list. Connect them into currentList if next non-empty line continues it.
      let nextNonEmptyIndex = -1;
      for (let j = i + 1; j < rawLines.length; j++) {
        if (rawLines[j].trim()) {
          nextNonEmptyIndex = j;
          break;
        }
      }
      if (nextNonEmptyIndex !== -1) {
        const nextTrimmed = rawLines[nextNonEmptyIndex].trim();
        const nextIsBullet = /^[-*•]\s+/.test(nextTrimmed);
        const nextIsNumbered = /^\d+\.\s+/.test(nextTrimmed);
        if (
          currentList &&
          ((currentList.type === 'bullet' && nextIsBullet) ||
            (currentList.type === 'numbered' && nextIsNumbered))
        ) {
          continue;
        }
      }
      flushList();
      continue;
    }

    // Check for bullet list item (- item, * item, • item)
    const bulletMatch = trimmed.match(/^[-*•]\s*(.*)$/);
    if (bulletMatch && (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ') || trimmed === '-' || trimmed === '*' || trimmed === '•')) {
      flushParagraph();
      if (!currentList || currentList.type !== 'bullet') {
        flushList();
        currentList = { type: 'bullet', items: [] };
      }
      const rawItemContent = bulletMatch[1] || '';
      currentList.items.push(parseInline(rawItemContent, paymentUrl, state));
      continue;
    }

    // Check for numbered list item (1. item, 2. item)
    const numberedMatch = trimmed.match(/^(\d+)\.\s*(.*)$/);
    if (numberedMatch) {
      flushParagraph();
      if (!currentList || currentList.type !== 'numbered') {
        flushList();
        currentList = { type: 'numbered', items: [] };
      }
      currentList.items.push({
        num: numberedMatch[1],
        nodes: parseInline(numberedMatch[2] || '', paymentUrl, state),
      });
      continue;
    }

    // Indented continuation line under an existing list
    if (currentList && /^\s{2,}|\t/.test(line) && trimmed) {
      const lastIdx = currentList.items.length - 1;
      if (lastIdx >= 0) {
        const extraNodes = parseInline(' ' + trimmed, paymentUrl, state);
        if (currentList.type === 'numbered') {
          currentList.items[lastIdx].nodes.push(...extraNodes);
        } else {
          currentList.items[lastIdx].push(...extraNodes);
        }
        continue;
      }
    }

    // Otherwise, regular paragraph text
    flushList();
    currentParagraphLines.push(line);
  }

  flushParagraph();
  flushList();

  return blocks;
}

export const renderMessage = (text, paymentUrl, isStreaming = false) => {
  if (!text) {
    if (isStreaming) {
      return (
        <span className="inline-block w-1.5 h-3.5 bg-[#C45C26] animate-pulse align-middle rounded-xs" />
      );
    }
    return null;
  }

  // Clean away any unwanted reasoning tags, monologue, or raw JSON
  const cleanedText = cleanAiText(text);
  if (!cleanedText) {
    if (isStreaming) {
      return (
        <span className="inline-block w-1.5 h-3.5 bg-[#C45C26] animate-pulse align-middle rounded-xs" />
      );
    }
    return null;
  }

  const blocks = parseBlocks(cleanedText, paymentUrl);
  if (blocks.length === 0) return null;

  const streamingCursor = isStreaming ? (
    <span
      key="streaming-cursor"
      className="inline-block w-1.5 h-3.5 ml-1 bg-[#C45C26] animate-pulse align-middle rounded-xs"
    />
  ) : null;

  return (
    <div className="space-y-2 leading-relaxed">
      {blocks.map((block, bIdx) => {
        const isLastBlock = bIdx === blocks.length - 1;

        if (block.type === 'bullet') {
          return (
            <div key={bIdx} className="my-1.5 space-y-1">
              {block.items.map((itemNodes, iIdx) => {
                const isLastItem = isLastBlock && iIdx === block.items.length - 1;
                return (
                  <div key={iIdx} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#C45C26] mt-2 shrink-0" />
                    <div className="flex-1 min-w-0 leading-normal">
                      {itemNodes.length > 0 ? itemNodes : <span className="inline-block w-1" />}
                      {isLastItem && streamingCursor}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        }

        if (block.type === 'numbered') {
          return (
            <div key={bIdx} className="my-1.5 space-y-1">
              {block.items.map((item, iIdx) => {
                const isLastItem = isLastBlock && iIdx === block.items.length - 1;
                return (
                  <div key={iIdx} className="flex items-start gap-2">
                    <span className="font-semibold text-xs text-[#C45C26] mt-0.5 shrink-0 min-w-[16px]">
                      {item.num}.
                    </span>
                    <div className="flex-1 min-w-0 leading-normal">
                      {item.nodes.length > 0 ? item.nodes : <span className="inline-block w-1" />}
                      {isLastItem && streamingCursor}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        }

        return (
          <div key={bIdx} className="leading-relaxed">
            {block.lines.map((lineNodes, lIdx) => {
              const isLastLine = isLastBlock && lIdx === block.lines.length - 1;
              return (
                <React.Fragment key={lIdx}>
                  {lineNodes}
                  {isLastLine && streamingCursor}
                  {lIdx < block.lines.length - 1 && <br />}
                </React.Fragment>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

export function extractPaymentUrl(text) {
  if (!text) return null;
  const md = text.match(/\]\((https?:\/\/[^\s)]+)\)/);
  if (md) return md[1];
  const raw = text.match(/https?:\/\/[^\s<>"')\]]+/);
  return raw ? raw[0] : null;
}
