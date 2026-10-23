"use client";

import { useState, useRef, useEffect } from "react";
import { Send, MessageSquare, User, Bot, Loader } from "lucide-react";
import { sendChatMessage, clearChatHistory, getChatHistory } from "../lib/api";

export default function ChatInterface({ notebookId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const sourcesRef = useRef([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // Load chat history when notebookId changes
  useEffect(() => {
    if (!notebookId) {
      setMessages([]);
      return;
    }

    const loadHistory = async () => {
      setIsLoadingHistory(true);
      try {
        const history = await getChatHistory(notebookId);
        if (Array.isArray(history)) {
          const mapped = history.map((msg) => ({
            role: msg.role,
            content: msg.content,
            sources: msg.sources_used || [],
          }));
          setMessages(mapped);
        }
      } catch (error) {
        console.error("Error loading chat history:", error);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    loadHistory();
  }, [notebookId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !notebookId) return;

    const userMessage = { role: "user", content: input.trim() };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);
    setStreamingContent("");
    sourcesRef.current = [];

    try {
      let fullContent = "";

      await sendChatMessage(notebookId, userMessage.content, {
        onContent: (chunk) => {
          fullContent += chunk;
          setStreamingContent(fullContent);
        },
        onSources: (srcList) => {
          sourcesRef.current = srcList || [];
        },
        onDone: (fullResponse) => {
          const assistantMessage = {
            role: "assistant",
            content: fullResponse || fullContent,
            sources: sourcesRef.current,
          };
          setMessages([...newMessages, assistantMessage]);
          setStreamingContent("");
          setIsLoading(false);
        },
      });
    } catch (error) {
      console.error("Chat error:", error);
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content:
            "Sorry, I encountered an error while processing your request. Please try again.",
        },
      ]);
      setStreamingContent("");
      setIsLoading(false);
    }
  };

  const clearChat = async () => {
    setMessages([]);
    setStreamingContent("");
    sourcesRef.current = [];
    if (notebookId) {
      try {
        await clearChatHistory(notebookId);
      } catch (e) {
        console.error("Error clearing chat history:", e);
      }
    }
  };

  return (
    <div className="surface-card rounded-xl h-[600px] flex flex-col overflow-hidden">
      {/* Header */}
      <div className="border-b border-slate-200/60 px-5 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center space-x-2">
          <MessageSquare className="h-5 w-5 text-blue-500" />
          <h2 className="text-base font-semibold text-slate-800">
            Chat with your documents
          </h2>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="text-xs text-slate-500 hover:text-slate-800 transition-colors"
          >
            Clear chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        {isLoadingHistory ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500/20 border-t-blue-500"></div>
          </div>
        ) : messages.length === 0 && !streamingContent ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-100 flex items-center justify-center">
              <MessageSquare className="h-8 w-8 text-slate-400" />
            </div>
            <p className="text-slate-600">Upload some documents and start asking questions!</p>
            <p className="text-sm text-slate-500 mt-2">
              I can help you understand and find information from your uploaded content.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex items-start space-x-3 animate-fade-in ${
                  message.role === "user" ? "justify-end" : ""
                }`}
              >
                {message.role === "assistant" && (
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200/50 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-blue-600" />
                    </div>
                  </div>
                )}
 
                <div
                  className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-2xl ${
                    message.role === "user"
                      ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white"
                      : "bg-slate-100 text-slate-800 border border-slate-200/50"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                  {/* Source citations */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-200/60">
                      <p className="text-xs text-slate-500 mb-1">Sources:</p>
                      {message.sources.map((src, i) => (
                        <span key={i} className="inline-block text-xs bg-slate-200 text-slate-600 px-2 py-0.5 rounded-md mr-1 mb-1 border border-slate-300/30">
                          📄 {src.source_name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
 
                {message.role === "user" && (
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center">
                      <User className="h-4 w-4 text-slate-600" />
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Streaming response */}
            {streamingContent && (
              <div className="flex items-start space-x-3 animate-fade-in">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200/50 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-blue-600" />
                  </div>
                </div>
                <div className="bg-slate-100 text-slate-800 px-4 py-3 rounded-2xl max-w-xs lg:max-w-md xl:max-w-lg border border-slate-200/50">
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{streamingContent}</p>
                  <span className="inline-block w-1.5 h-4 bg-blue-500 animate-pulse rounded-sm ml-0.5" />
                </div>
              </div>
            )}
          </>
        )}
 
        {isLoading && !streamingContent && (
          <div className="flex items-start space-x-3 animate-fade-in">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200/50 flex items-center justify-center">
                <Loader className="h-4 w-4 text-blue-600 animate-spin" />
              </div>
            </div>
            <div className="bg-slate-100 px-4 py-3 rounded-2xl border border-slate-200/50">
              <div className="flex items-center space-x-2">
                <Loader className="h-4 w-4 text-blue-600 animate-spin" />
                <span className="text-sm text-slate-500">Thinking...</span>
              </div>
            </div>
          </div>
        )}
 
        <div ref={messagesEndRef} />
      </div>
 
      {/* Input */}
      <div className="border-t border-slate-200/60 p-4 flex-shrink-0">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={notebookId ? "Ask a question about your documents..." : "Select a notebook first..."}
            className="flex-1 px-4 py-2.5 input-dark rounded-xl text-sm"
            disabled={isLoading || !notebookId}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading || !notebookId}
            className="btn-primary px-4 py-2.5 rounded-xl flex items-center space-x-2"
          >
            <Send className="h-4 w-4" />
            <span className="hidden sm:inline text-sm">Send</span>
          </button>
        </form>
      </div>
    </div>
  );
}

