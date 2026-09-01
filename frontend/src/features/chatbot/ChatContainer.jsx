import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X } from 'lucide-react';
import { useStore } from '../../store/useStore';
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import { ChatHeader } from "./ChatHeader";
import { renderMessage } from "./renderMessage";

export function AgentWidget() {
  const [input, setInput] = useState('');
  const { aiMessages, aiMessagesLastUpdated, isAiTyping, sendAiMessage, isAiConnected, comboOffer, connectAgent, disconnectAgent, isAgentOpen, setIsAgentOpen } = useStore();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    connectAgent();
    if (aiMessagesLastUpdated && (Date.now() - aiMessagesLastUpdated > 24 * 60 * 60 * 1000)) {
      useStore.setState({ aiMessages: [], aiMessagesLastUpdated: Date.now(), comboOffer: null });
    } else if (!aiMessagesLastUpdated) {
      useStore.setState({ aiMessagesLastUpdated: Date.now() });
    }
    return () => disconnectAgent();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [aiMessages, isAgentOpen, isAiTyping]);

  const handleSend = (e) => {
    e.preventDefault();
    if (input.trim()) { sendAiMessage(input); setInput(''); }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {isAgentOpen && (
        <div className="mb-4 w-[90vw] sm:w-[450px] bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden flex flex-col transition-all h-[70vh]">
          <ChatHeader isAiConnected={isAiConnected} setIsAgentOpen={setIsAgentOpen} />
          <ChatMessages aiMessages={aiMessages} isAiTyping={isAiTyping} comboOffer={comboOffer} messagesEndRef={messagesEndRef} renderMessage={renderMessage} />
          <ChatInput input={input} setInput={setInput} handleSend={handleSend} isAiConnected={isAiConnected} />
        </div>
      )}
      <button onClick={() => setIsAgentOpen(!isAgentOpen)} className="bg-slate-900 hover:bg-slate-800 text-white p-4 rounded-full shadow-lg transition-all flex items-center justify-center">
        {isAgentOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>
    </div>
  );
}
