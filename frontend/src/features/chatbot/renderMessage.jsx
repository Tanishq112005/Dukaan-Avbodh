import React from 'react';

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
  let seenPaymentLink = false;
  const lines = text.split('\n');

  const renderedLines = lines
    .map((line, i) => {
      const parts = line.split(URL_SPLIT);

      const nodes = parts
        .map((part, j) => {
          if (!part) return null;

          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={j} className="font-bold">{part.slice(2, -2)}</strong>;
          }

          const md = part.match(/^\[(.*?)\]\((https?:\/\/[^\s)]+)\)$/);
          const url = md ? md[2] : (/^https?:\/\//.test(part) ? part : null);

          if (url) {
            const isPayment = PAYMENT_PATTERN.test(url) || url === paymentUrl;
            if (isPayment) {
              // Hide every payment link from inline text —
              // the "Pay securely" button below already handles it.
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

      // Skip rendering a line entirely if it was *only* a payment link
      // (avoids leaving a stray blank line / <br/>)
      if (nodes.length === 0) return null;

      return (
        <React.Fragment key={i}>
          {nodes}
        </React.Fragment>
      );
    })
    .filter(Boolean);

  // Re-add line breaks only between remaining, non-empty lines
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