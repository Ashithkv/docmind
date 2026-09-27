import { useEffect, useRef, useState } from "react";
import { askQuestion } from "../services/api";
import SourceCitations from "./SourceCitations";

export default function ChatWindow({ hasDocuments }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isAsking) return;

    const userMessage = { role: "user", text: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setIsAsking(true);

    try {
      const result = await askQuestion(trimmed);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: result.answer,
          sources: result.sources,
          foundContext: result.found_context,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: err.message, isError: true },
      ]);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <div className="chat-section">
      <h2>Ask a Question</h2>
      <div className="chat-window">
        {messages.length === 0 && (
          <p className="empty-hint">
            {hasDocuments
              ? "Ask a question about your uploaded documents."
              : "Upload a PDF above to start asking questions."}
          </p>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message chat-message-${msg.role}`}>
            <div className={`chat-bubble ${msg.isError ? "chat-bubble-error" : ""}`}>
              <p>{msg.text}</p>
            </div>
            {msg.role === "assistant" && !msg.isError && (
              <SourceCitations sources={msg.sources} />
            )}
          </div>
        ))}
        {isAsking && (
          <div className="chat-message chat-message-assistant">
            <div className="chat-bubble chat-bubble-loading">Thinking&hellip;</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={
            hasDocuments ? "Ask about your documents…" : "Upload a document first…"
          }
          disabled={!hasDocuments || isAsking}
        />
        <button type="submit" disabled={!hasDocuments || isAsking || !question.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
