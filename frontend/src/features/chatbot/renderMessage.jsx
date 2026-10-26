import React from 'react';
import { cleanAiText } from '../../lib/textCleaning';

const URL_SPLIT = /(\*\*.*?\*\*|\[.*?\]\(https?:\/\/[^\s)]+\)|https?:\/\/[^\s<>"')\]]+)/g;
const PAYMENT_PATTERN = /razorpay|rzp\.io|rzp_/i;

function Linkish({ href, children, className }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={className || "text-[#C45C26] hover:text-[#a3481b] underline underline-offset-2 font-semibold break-all"}
    >
      {children}
    </a>
  );
}

export const renderMessage = (text, paymentUrl) => {
  if (!text) return null;

  // Clean away any unwanted reasoning tags, monologue, or raw JSON
  const cleanedText = cleanAiText(text);
  if (!cleanedText) return null;

  let seenPaymentLink = false;
  const lines = cleanedText.split('\n');

  const renderedLines = lines
    .map((line, i) => {
      const trimmed = line.trim();
      const isBullet = trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ');
      const content = isBullet ? trimmed.replace(/^[-*•]\s+/, '') : line;

      const parts = content.split(URL_SPLIT);

      const nodes = parts
        .map((part, j) => {
          if (!part) return null;

          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={j} className="font-bold text-stone-900">{part.slice(2, -2)}</strong>;
          }

          const md = part.match(/^\[(.*?)\]\((https?:\/\/[^\s)]+)\)$/);
          const url = md ? md[2] : (/^https?:\/\//.test(part) ? part : null);

          if (url) {
            const isPayment = PAYMENT_PATTERN.test(url) || url === paymentUrl;
            if (isPayment) {
              if (seenPaymentLink) return null;
              seenPaymentLink = true;
              return null;
            }
            const label = md ? md[1] : url;
            return <Linkish key={j} href={url}>{label}</Linkish>;
          }

          return <span key={j}>{part}</span>;
        })
        .filter(Boolean);

      if (nodes.length === 0) return null;

      if (isBullet) {
        return (
          <div key={i} className="flex items-start gap-2 my-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[#C45C26] mt-2 flex-shrink-0" />
            <div className="flex-1">{nodes}</div>
          </div>
        );
      }

      return (
        <React.Fragment key={i}>
          {nodes}
        </React.Fragment>
      );
    })
    .filter(Boolean);

  return renderedLines.map((node, idx) => (
    <React.Fragment key={idx}>
      {node}
      {idx < renderedLines.length - 1 && <br />}
    </React.Fragment>
  ));
};

export function extractPaymentUrl(text) {
  if (!text) return null;
  const md = text.match(/\]\((https?:\/\/[^\s)]+)\)/);
  if (md) return md[1];
  const raw = text.match(/https?:\/\/[^\s<>"')\]]+/);
  return raw ? raw[0] : null;
}
