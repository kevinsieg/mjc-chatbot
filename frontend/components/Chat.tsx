"use client";

import { memo, useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import { brand } from "@/brand/brand";
import styles from "./Chat.module.css";

type Role = "user" | "assistant";

export type UiMessage = { id: string; role: Role; content: string; sentAt: Date };

function createMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

function formatTime(date: Date): string {
  const h = date.getHours().toString().padStart(2, "0");
  const m = date.getMinutes().toString().padStart(2, "0");
  return `${h}:${m}`;
}

function SendIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function GoellanAvatar({
  size = 36,
  className = styles.avatar,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <Image
      className={className}
      src={brand.assets.mascot}
      alt="Goëllan"
      width={size}
      height={Math.round(size * 1.123)}
      style={{ width: size, height: "auto" }}
    />
  );
}

function TypingDots() {
  return (
    <span className={styles.typing} aria-label="En cours de rédaction">
      <span />
      <span />
      <span />
    </span>
  );
}

const UserBubble = memo(function UserBubble({ message }: { message: UiMessage }) {
  return (
    <div className={styles.rowUser}>
      <div className={styles.bubbleUser}>
        <p className={styles.text}>{message.content}</p>
        <time className={styles.time} dateTime={message.sentAt.toISOString()}>
          {formatTime(message.sentAt)}
        </time>
      </div>
    </div>
  );
});

const BotBubble = memo(function BotBubble({ message }: { message: UiMessage }) {
  return (
    <div className={styles.rowBot}>
      <GoellanAvatar />
      <div className={styles.bubbleBot}>
        <p className={styles.text}>{message.content}</p>
        <time className={styles.time} dateTime={message.sentAt.toISOString()}>
          {formatTime(message.sentAt)}
        </time>
      </div>
    </div>
  );
});

type ChatProps = {
  /** When set, sent as system_prompt on each chat request (home page override). */
  systemPromptOverride?: string;
};

export function Chat({ systemPromptOverride }: ChatProps = {}) {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending, scrollToBottom]);

  // Cancel any inflight request on unmount
  useEffect(() => {
    return () => { abortRef.current?.abort(); };
  }, []);

  // Auto-resize textarea as content grows/shrinks
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [draft]);

  const send = useCallback(async () => {
    if (sending) return;
    const text = draft.trim();
    if (!text) return;
    setError(null);
    const userMsg: UiMessage = { id: createMessageId(), role: "user", content: text, sentAt: new Date() };
    const nextThread = [...messages, userMsg];
    setMessages(nextThread);
    setDraft("");
    setSending(true);
    abortRef.current = new AbortController();
    try {
      const res = await fetch("/api/backend/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: nextThread.map((m) => ({ role: m.role, content: m.content })),
          ...(systemPromptOverride !== undefined
            ? { system_prompt: systemPromptOverride }
            : {}),
        }),
        signal: abortRef.current.signal,
      });
      if (!res.ok) {
        let detail = res.statusText;
        try {
          const b = (await res.json()) as { detail?: unknown };
          if (b.detail !== undefined) detail = JSON.stringify(b.detail);
        } catch {
          /* ignore non-JSON error bodies */
        }
        throw new Error(`HTTP ${res.status}: ${detail}`);
      }
      const data = (await res.json()) as { reply: string };
      if (typeof data.reply !== "string" || !data.reply) {
        throw new Error("Invalid response: missing reply string");
      }
      setMessages((prev) => [
        ...prev,
        { id: createMessageId(), role: "assistant", content: data.reply, sentAt: new Date() },
      ]);
    } catch (e: unknown) {
      if (e instanceof Error && e.name === "AbortError") return;
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
      setDraft(text);
    } finally {
      setSending(false);
      abortRef.current = null;
    }
  }, [draft, messages, sending, systemPromptOverride]);

  return (
    <section className={styles.wrap} aria-label="Conversation avec le chatbot">
      <div ref={listRef} className={styles.messages}>
        {messages.length === 0 ? (
          <div className={styles.welcome}>
            <GoellanAvatar size={80} className={styles.welcomeAvatar} />
            <div className={styles.welcomeBubble}>
              <p>
                Bonjour&nbsp;! Je suis <strong>Goëllan</strong>, l&apos;assistant de la{" "}
                <strong>MJC de Fécamp</strong>. Posez-moi une question sur les
                activités, les horaires ou les inscriptions&nbsp;!
              </p>
            </div>
          </div>
        ) : (
          messages.map((m) =>
            m.role === "user" ? (
              <UserBubble key={m.id} message={m} />
            ) : (
              <BotBubble key={m.id} message={m} />
            )
          )
        )}

        {sending && (
          <div className={styles.rowBot}>
            <GoellanAvatar />
            <div className={styles.bubbleBot}>
              <TypingDots />
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      <form
        className={styles.form}
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <label className={styles.srOnly} htmlFor="chat-input">
          Votre message
        </label>
        <textarea
          ref={textareaRef}
          id="chat-input"
          className={styles.input}
          rows={1}
          value={draft}
          disabled={sending}
          placeholder="Écrivez votre message…"
          enterKeyHint="send"
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
        />
        <button
          type="submit"
          className={styles.send}
          disabled={sending || !draft.trim()}
          aria-label="Envoyer"
        >
          <SendIcon />
        </button>
      </form>
    </section>
  );
}
