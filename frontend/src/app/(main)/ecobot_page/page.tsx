"use client";

import { useState, useEffect, useRef } from "react";
import { Knewave, Abhaya_Libre, Gotu } from "next/font/google";
import { Send, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { MobileNavMenu } from "@/components/MobileNavMenu";
import { PRIMARY_NAV_LINKS } from "@/constants/navLinks";

const knewave = Knewave({ subsets: ["latin"], weight: ["400"] });
const abhaya = Abhaya_Libre({ 
  subsets: ["latin"], 
  weight: ["400", "500", "600", "700"] 
});
const gotu = Gotu({ subsets: ["latin"], weight: ["400"] });

type Message = {
  sender: "user" | "bot";
  text: string;
  time: string;
  isLoading?: boolean;
};

export default function EcobotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: "Hi! I'm EcoBot, your sustainable travel assistant. Ask me anything about eco-friendly travel, destinations, or carbon footprint tips! 🌱",
      time: getCurrentTime(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  function getCurrentTime() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, "0");
    const m = String(now.getMinutes()).padStart(2, "0");
    return `${h}:${m}`;
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const time = getCurrentTime();
    const userText = input.trim();

    const userMsg: Message = { sender: "user", text: userText, time };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    // Add loading indicator
    const loadingMsg: Message = {
      sender: "bot",
      text: "",
      time,
      isLoading: true,
    };
    setMessages((prev) => [...prev, loadingMsg]);

    try {
      const userId = typeof window !== "undefined" 
        ? parseInt(localStorage.getItem("user_id") || "1") 
        : 1;
      const roomId = 1; // Default room for chatbot

      const data = await api.sendBotMessage(userId, roomId, userText);

      // Remove loading message and add actual response
      setMessages((prev) => {
        const withoutLoading = prev.filter((m) => !m.isLoading);
        return [
          ...withoutLoading,
          {
            sender: "bot",
            text: data.response || "I'm not sure how to respond to that.",
            time: getCurrentTime(),
          },
        ];
      });
    } catch (error) {
      console.error("Chatbot error:", error);
      setMessages((prev) => {
        const withoutLoading = prev.filter((m) => !m.isLoading);
        return [
          ...withoutLoading,
          {
            sender: "bot",
            text: "Sorry, I'm having trouble connecting right now. Please try again.",
            time: getCurrentTime(),
          },
        ];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      setTimeout(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      }, 100);
    }
  }, [messages]);

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-100">
      <div className="w-full max-w-md bg-white min-h-screen flex flex-col shadow-lg">
        {/* HEADER */}
        <header className="bg-green-500 px-4 py-4 flex-shrink-0">
          <h1 className={`${knewave.className} text-2xl text-white text-center`}>
            EcomoveX
          </h1>
        </header>

        {/* CHAT AREA */}
        <main
          ref={scrollRef}
          className="flex-1 px-4 py-4 overflow-y-auto pb-28"
        >
          <div className="flex flex-col gap-3">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2 items-end ${
                  msg.sender === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {/* BOT AVATAR */}
                {msg.sender === "bot" && (
                  <div className="flex-shrink-0 mb-5">
                    <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center text-xs">
                      🤖
                    </div>
                  </div>
                )}

                {/* MESSAGE BUBBLE */}
                <div
                  className={`flex flex-col max-w-[60%] ${
                    msg.sender === "user" ? "items-end" : "items-start"
                  }`}
                >
                  <div
                    className={`${abhaya.className} px-3 py-2.5 rounded-2xl break-words ${
                      msg.sender === "user"
                        ? "bg-green-500 bg-opacity-80 text-white rounded-br-sm"
                        : "bg-white border border-gray-200 text-gray-800 rounded-bl-sm"
                    }`}
                  >
                    {msg.isLoading ? (
                      <div className="flex items-center gap-2">
                        <Loader2 size={14} className="animate-spin text-green-600" />
                        <span className={`${gotu.className} text-xs text-gray-500`}>
                          Thinking...
                        </span>
                      </div>
                    ) : (
                      <span className="text-sm leading-relaxed whitespace-pre-wrap">
                        {msg.text}
                      </span>
                    )}
                  </div>
                  <span
                    className={`${gotu.className} text-[10px] text-gray-400 mt-1 px-1`}
                  >
                    {msg.time}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </main>

        {/* INPUT SECTION */}
        <div className="border-t border-gray-200 bg-white p-3 flex-shrink-0 pb-20">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask about eco-travel..."
              rows={1}
              disabled={isLoading}
              className={`${abhaya.className} flex-1 resize-none rounded-xl px-3 py-2.5 bg-gray-50 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:bg-white transition-all disabled:opacity-50 max-h-32 text-sm border border-gray-200 overflow-hidden`}
              style={{
                height: "auto",
                minHeight: "40px",
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = "auto";
                target.style.height = `${Math.min(target.scrollHeight, 128)}px`;
              }}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="flex-shrink-0 w-10 h-10 rounded-xl bg-green-500 hover:bg-green-600 active:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
            >
              {isLoading ? (
                <Loader2 size={18} className="text-white animate-spin" />
              ) : (
                <Send size={16} className="text-white" />
              )}
            </button>
          </div>
        </div>

        {/* FOOTER NAV */}
        <MobileNavMenu items={PRIMARY_NAV_LINKS} activeKey="ecobot" />
      </div>
    </div>
  );
}