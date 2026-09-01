import React from 'react';

export const renderMessage = (text) => {
  if (!text) return null;
  return text.split('\n').map((line, i) => {
    const parts = line.split(/(\*\*.*?\*\*|\[.*?\]\(.*?\))/g);
    return (
      <React.Fragment key={i}>
        {parts.map((part, j) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={j} className="font-bold">{part.slice(2, -2)}</strong>;
          }
          const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/);
          if (linkMatch) {
            return <a key={j} href={linkMatch[2]} className="text-indigo-600 hover:text-indigo-700 underline font-medium">{linkMatch[1]}</a>;
          }
          return <span key={j}>{part}</span>;
        })}
        {i < text.split('\n').length - 1 && <br />}
      </React.Fragment>
    );
  });
};
