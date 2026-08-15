"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { apiClient } from "@/services/api";
import { SourceCitation } from "@/components/SourceCitation";
import { SafetyBanner } from "@/components/SafetyBanner";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { clsx } from "clsx";
import type { ChatMessage } from "@/types/health";

export function ChatWindow() {
  const { session } = useAuth();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingSession, setLoadingSession] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Initialize session
  useEffect(() => {
    if (!session) return;
    apiClient.createChatSession(session.access_token).then((res) => {
      setSessionId(res.session_id);
      setLoadingSession(false);
    });
  }, [session]);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !sessionId || !session || sending) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages((m) => [...m, userMessage]);
    setInput("");
    setSending(true);

    try {
      const response = await apiClient.sendMessage(
        sessionId,
        userMessage.content,
        session.access_token
      );
      setMessages((m) => [...m, { ...response, id: Date.now().toString() + "_ai" }]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: Date.now().toString() + "_err",
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
          risk_level: "low",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  if (loadingSession) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mr-2" />
        Initializing chat…
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-16 text-slate-500">
            <div className="w-16 h-16 rounded-2xl bg-surface-elevated border border-surface-border flex items-center justify-center mx-auto mb-4">
              <Bot className="w-8 h-8 text-brand-400" />
            </div>
            <p className="font-medium text-slate-400">How can I help you today?</p>
            <p className="text-sm mt-1">Ask about your lab results, medications, or health trends.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={clsx(
              "flex gap-3 max-w-3xl animate-fade-in",
              msg.role === "user" ? "ml-auto flex-row-reverse" : ""
            )}
          >
            {/* Avatar */}
            <div className={clsx(
              "w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center mt-0.5",
              msg.role === "user"
                ? "bg-brand-600/20 border border-brand-500/30"
                : "bg-surface-elevated border border-surface-border"
            )}>
              {msg.role === "user"
                ? <User className="w-4 h-4 text-brand-400" />
                : <Bot className="w-4 h-4 text-slate-400" />}
            </div>

            {/* Bubble */}
            <div className={clsx(
              "flex flex-col gap-1.5 max-w-[85%]",
              msg.role === "user" ? "items-end" : "items-start"
            )}>
              <div className={clsx(
                "px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap",
                msg.role === "user"
                  ? "bg-brand-600 text-white rounded-tr-sm"
                  : "bg-surface-card border border-surface-border text-slate-200 rounded-tl-sm"
              )}>
                {msg.content}
              </div>
              {msg.citations && msg.citations.length > 0 && (
                <SourceCitation citations={msg.citations} />
              )}
              {msg.risk_level && msg.risk_level !== "low" && (
                <SafetyBanner riskLevel={msg.risk_level as "medium" | "high"} />
              )}
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-xl bg-surface-elevated border border-surface-border flex items-center justify-center">
              <Bot className="w-4 h-4 text-slate-400" />
            </div>
            <div className="bg-surface-card border border-surface-border rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1.5 items-center h-5">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-2 h-2 rounded-full bg-slate-500 animate-pulse"
                    style={{ animationDelay: `${i * 200}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-surface-border px-6 py-4 flex-shrink-0">
        <form onSubmit={sendMessage} className="flex gap-3">
          <input
            id="chat-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your health reports…"
            disabled={sending}
            className="input-field flex-1"
          />
          <button
            id="chat-send"
            type="submit"
            disabled={!input.trim() || sending}
            className="btn-primary px-4 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </form>
        <p className="text-xs text-slate-600 mt-2 text-center">
          Clinexa AI can make mistakes. Do not rely on it for medical decisions.
        </p>
      </div>
    </div>
  );
}
