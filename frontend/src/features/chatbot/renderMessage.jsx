import React from 'react';

const URL_SPLIT = /(\*\*.*?\*\*|\[.*?\]\(https?:\/\/[^\s)]+\)|https?:\/\/[^\s<>"')\]]+)/g;

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

export const renderMessage = (text) => {
  if (!text) return null;
  const lines = text.split('\n');
  return lines.map((line, i) => {
    const parts = line.split(URL_SPLIT);
    return (
      <React.Fragment key={i}>
        {parts.map((part, j) => {
          if (!part) return null;
          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={j} className="font-bold">{part.slice(2, -2)}</strong>;
          }
          const md = part.match(/^\[(.*?)\]\((https?:\/\/[^\s)]+)\)$/);
          if (md) {
            return <Linkish key={j} href={md[2]}>{md[1]}</Linkish>;
          }
          if (/^https?:\/\//.test(part)) {
            const label = /razorpay|rzp\.io|rzp_/.test(part) ? 'Pay now' : part;
            return <Linkish key={j} href={part}>{label === 'Pay now' ? 'Pay now' : part}</Linkish>;
          }
          return <span key={j}>{part}</span>;
        })}
        {i < lines.length - 1 && <br />}
      </React.Fragment>
    );
  });
};

export function extractPaymentUrl(text) {
  if (!text) return null;
  const md = text.match(/\]\((https?:\/\/[^\s)]+)\)/);
  if (md) return md[1];
  const raw = text.match(/https?:\/\/[^\s<>"')\]]+/);
  return raw ? raw[0] : null;
}
