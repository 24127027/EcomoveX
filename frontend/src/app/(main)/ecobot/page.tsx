"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { Knewave } from "next/font/google";
import icon from "@/app/icon.png";


const knewave = Knewave({ subsets: ["latin"], weight: ["400"] });

type Message = {
  sender: "user" | "bot";
  text: string;
  time: string;
};

export default function EcobotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const getCurrentTime = () => {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, "0");
    const m = String(now.getMinutes()).padStart(2, "0");
    return `${h}:${m}`;
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const time = getCurrentTime();
    const userText = input;

    const userMsg: Message = { sender: "user", text: userText, time };
    setMessages(prev => [...prev, userMsg]);
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/chatbot/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: 1,
          room_id: 1,
          message: userText,
        }),
      });

      const data = await res.json();

      const botMsg: Message = {
        sender: "bot",
        text: data.response || "I'm not sure how to respond.",
        time: getCurrentTime(),
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      setMessages(prev => [
        ...prev,
        { sender: "bot", text: "Server error. Try again.", time: getCurrentTime() },
      ]);
    }
  };

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div className="min-h-screen flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-white h-screen flex flex-col overflow-hidden shadow-xl">
        
        {/* HEADER */}
        <header className="bg-[#53B552] flex items-center px-4 py-4 shadow-md">
          <Image src={icon} alt="EcomoveX Logo" width={40} height={40} priority className="rounded-full overflow-hidden"/>
          <h1 className={`${knewave.className} ml-3 text-white font-bold text-xl`}>
            EcomoveX Chatbot
          </h1>
        </header>

        {/* CHAT AREA */}
        <main
          ref={scrollRef}
          className="flex-1 p-4 overflow-y-auto flex flex-col gap-3 bg-gray-50"
        >
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-2 items-end ${
                msg.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {/* BOT AVATAR */}
              {msg.sender === "bot" && (
                <Image
                  src={icon}
                  alt="Bot"
                  width={32}
                  height={32}
                  className="rounded-full"
                />
              )} 

              {/* MESSAGE BUBBLE + TIME */}
              <div className="flex flex-col max-w-[70%]">
                <div
                  className={`p-3 rounded-xl break-words ${
                    msg.sender === "user"
                      ? "bg-green-200 text-black self-end"
                      : "bg-white text-gray-700 text-sm self-start"
                  }`}
                >
                  {msg.text}
                </div>
                <span className="text-[10px] text-gray-500 mt-1 self-end">{msg.time}</span>
              </div>

              {/* USER AVATAR */}
              {msg.sender === "user" && (
                <Image
                  src="/images/default-avatar.png"
                  alt="User"
                  width={32}
                  height={32}
                  className="rounded-full"
                />
              )}
            </div>
          ))}
        </main>

        {/* INPUT BOX */}
        <div className="flex p-4 border-t bg-gray-100">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 rounded-l-full px-4 py-2 text-white bg-green-600 focus:outline-none"
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />

          <button
            onClick={sendMessage}
            className="bg-white text-green-600 px-4 rounded-r-full font-semibold hover:bg-gray-100"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
