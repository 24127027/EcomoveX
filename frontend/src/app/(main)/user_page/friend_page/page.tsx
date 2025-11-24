"use client";

import React, { useEffect, useState, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  ArrowLeft,
  UserPlus,
  UserMinus,
  Check,
  X,
  Search,
  Users,
  Loader2,
  User,
  Bot,
  Home,
  MapPin,
  AlertTriangle,
  Send,
  MessageCircle, // Icon chat
} from "lucide-react";
import { Jost } from "next/font/google";
import { api, FriendResponse, ChatMessage } from "@/lib/api";

const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "700"] });

export default function FriendsPage() {
  // --- STATE CƠ BẢN ---
  const [activeTab, setActiveTab] = useState<"friends" | "requests" | "sent">(
    "friends"
  );
  const [friends, setFriends] = useState<FriendResponse[]>([]);
  const [requests, setRequests] = useState<FriendResponse[]>([]);
  const [sentRequests, setSentRequests] = useState<FriendResponse[]>([]);

  const [loading, setLoading] = useState(true);
  const [inputFriendId, setInputFriendId] = useState("");
  const [addLoading, setAddLoading] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<{
    text: string;
    type: "success" | "error";
  } | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);

  // --- STATE CHO CHAT (MỚI) ---
  const [activeChatFriend, setActiveChatFriend] =
    useState<FriendResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const socketRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null); // Để auto scroll

  // --- 1. FETCH DATA BAN ĐẦU ---
  const fetchData = async () => {
    try {
      setLoading(true);
      const currentUser = await api.getUserProfile();
      if (currentUser) setCurrentUserId(currentUser.id);

      const [friendsData, requestsData, sentData] = await Promise.all([
        api.getFriends(),
        api.getPendingRequests(),
        api.getSentRequests(),
      ]);

      setFriends(friendsData);
      setRequests(requestsData);
      setSentRequests(sentData);
    } catch (error) {
      console.error("Error loading friends:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // --- 2. LOGIC SCROLL CHAT ---
  // Mỗi khi messages thay đổi, tự cuộn xuống dưới cùng
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // --- 3. LOGIC WEBSOCKET & CHAT ---

  // Hàm mở Chat
  const openChat = async (friend: FriendResponse) => {
    if (!currentUserId) return;
    setActiveChatFriend(friend);
    setMessages([]);

    const friendId =
      currentUserId === friend.user_id ? friend.friend_id : friend.user_id;

    try {
      let roomId: number;

      // BƯỚC 1: Lấy tất cả phòng và tìm thủ công (Client-side filtering)
      // Vì backend không có API "check room", ta phải lấy hết về rồi tự soi.
      const allRooms = await api.getAllRooms();

      // Tìm phòng nào có chứa friendId trong danh sách thành viên
      const existingRoom = allRooms.find(
        (room) => room.member_ids && room.member_ids.includes(friendId)
      );

      if (existingRoom) {
        // -> Đã có phòng: Dùng luôn ID đó
        console.log("Found existing room:", existingRoom.id);
        roomId = existingRoom.id;
      } else {
        // -> Chưa có: Gọi API tạo phòng mới (Dùng hàm create_room có sẵn)
        console.log("No room found. Creating new room...");
        // Tạo phòng tên "Chat" với thành viên là friendId
        const newRoom = await api.createGroupRoom("Private Chat", [friendId]);
        roomId = newRoom.id;
      }

      // BƯỚC 2: Lấy lịch sử & Kết nối Socket (Giữ nguyên)
      const history = await api.getChatHistory(roomId);
      setMessages(history.reverse());

      connectWebSocket(roomId);
    } catch (error) {
      console.error("Failed to open chat:", error);
      setFeedback({ text: "Could not connect to chat", type: "error" });
    }
  };

  const connectWebSocket = (roomId: number) => {
    // Đóng kết nối cũ nếu có
    if (socketRef.current) {
      socketRef.current.close();
    }

    const wsUrl = api.getWebSocketUrl(roomId);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("Connected to Chat WebSocket");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      setMessages((prev) => {
        const isDuplicate = prev.some((msg) => msg.id === data.id);
        if (isDuplicate) {
          return prev;
        }
        return [...prev, data];
      });
    };

    ws.onclose = () => {
      console.log("Chat WebSocket disconnected");
    };

    ws.onerror = (error) => {
      console.error("WebSocket Error:", error);
    };

    socketRef.current = ws;
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim() || !socketRef.current) return;

    // Gửi tin nhắn qua Socket
    const payload = { content: inputMessage.trim() };
    socketRef.current.send(JSON.stringify(payload));

    setInputMessage("");
    // Lưu ý: Không cần setMessages thủ công ở đây,
    // vì Server sẽ broadcast lại tin nhắn đó và ws.onmessage sẽ hứng nó.
  };

  const closeChat = () => {
    setActiveChatFriend(null);
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  };

  // --- 4. LOGIC QUẢN LÝ BẠN BÈ (CŨ) ---
  const handleSendRequest = async () => {
    setFeedback(null);
    if (!inputFriendId.trim()) {
      setFeedback({ text: "Please enter a User ID", type: "error" });
      return;
    }
    const idToSend = parseInt(inputFriendId);
    if (isNaN(idToSend)) {
      setFeedback({ text: "User ID must be a number", type: "error" });
      return;
    }
    if (currentUserId && idToSend === currentUserId) {
      setFeedback({ text: "You cannot add yourself", type: "error" });
      return;
    }

    const isAlreadySent = sentRequests.some(
      (req) => req.friend_id === idToSend
    );
    if (isAlreadySent) {
      setFeedback({ text: "Request already sent!", type: "error" });
      return;
    }

    const isAlreadyFriend = friends.some((f) => {
      const displayId = currentUserId === f.user_id ? f.friend_id : f.user_id;
      return displayId === idToSend;
    });

    if (isAlreadyFriend) {
      setFeedback({ text: "Already your friend", type: "error" });
      return;
    }

    try {
      setAddLoading(true);
      await api.sendFriendRequest(idToSend);
      setFeedback({ text: "Request sent successfully", type: "success" });
      setInputFriendId("");
      fetchData();
    } catch (error: any) {
      // ... (Giữ nguyên logic handle error cũ của bạn)
      setFeedback({ text: "Failed to send request", type: "error" });
    } finally {
      setAddLoading(false);
    }
  };

  const handleUnfriendClick = (friendId: number) => {
    setFeedback(null);
    setDeleteTargetId(friendId);
  };

  const confirmDeleteFriend = async () => {
    if (!deleteTargetId) return;
    try {
      await api.unfriend(deleteTargetId);
      setFeedback({ text: "Friend removed", type: "success" });
      fetchData();
    } catch (e) {
      setFeedback({ text: "Failed to remove friend", type: "error" });
    } finally {
      setDeleteTargetId(null);
    }
  };

  const handleAccept = async (id: number) => {
    try {
      await api.acceptFriendRequest(id);
      fetchData();
    } catch (e) {}
  };
  const handleReject = async (id: number) => {
    try {
      await api.rejectFriendRequest(id);
      fetchData();
    } catch (e) {}
  };
  const handleCancelRequest = async (id: number) => {
    try {
      await api.unfriend(id);
      fetchData();
    } catch (e) {}
  };

  const getDisplayId = (item: FriendResponse) => {
    if (!currentUserId) return item.friend_id;
    return item.user_id === currentUserId ? item.friend_id : item.user_id;
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* --- MODAL XÓA BẠN --- */}
        {deleteTargetId && (
          <div className="absolute inset-0 bg-black/60 z-50 flex items-center justify-center p-6 animate-in fade-in duration-200">
            <div className="bg-white rounded-3xl p-6 w-full max-w-sm shadow-2xl">
              <div className="text-center">
                <AlertTriangle
                  className="mx-auto text-red-500 mb-4"
                  size={32}
                />
                <h3 className="text-xl font-bold mb-2">Unfriend User?</h3>
                <p className="text-gray-500 mb-6">
                  Are you sure you want to remove ID: {deleteTargetId}?
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setDeleteTargetId(null)}
                    className="flex-1 py-3 bg-gray-100 rounded-xl font-bold"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmDeleteFriend}
                    className="flex-1 py-3 bg-red-500 text-white rounded-xl font-bold"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- MODAL CHAT (MỚI) --- */}
        {activeChatFriend && (
          <div className="absolute inset-0 z-40 bg-[#F5F7F5] flex flex-col animate-in slide-in-from-right duration-300">
            {/* Chat Header */}
            <div className="bg-[#E3F1E4] p-4 pt-8 flex items-center shadow-sm shrink-0">
              <button
                onClick={closeChat}
                className="p-2 bg-white rounded-full text-green-700 mr-3 hover:bg-green-50"
              >
                <ArrowLeft size={20} />
              </button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white relative overflow-hidden border-2 border-green-200">
                  <Image
                    src="/images/default-avatar.png"
                    alt="Avt"
                    fill
                    className="object-cover"
                  />
                </div>
                <div>
                  <h3 className={`${jost.className} font-bold text-gray-800`}>
                    User {getDisplayId(activeChatFriend)}
                  </h3>
                  <span className="text-xs text-green-600 flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>{" "}
                    Online
                  </span>
                </div>
              </div>
            </div>

            {/* Chat Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#F5F7F5]">
              {messages.length === 0 ? (
                <div className="text-center mt-20 text-gray-400 text-sm">
                  Send a message to start chatting...
                </div>
              ) : (
                messages.map((msg, index) => {
                  const isMe = msg.sender_id === currentUserId;
                  return (
                    <div
                      key={index}
                      className={`flex ${
                        isMe ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[75%] p-3 rounded-2xl text-sm wrap-break-words ${
                          isMe
                            ? "bg-[#53B552] text-white rounded-tr-none shadow-md"
                            : "bg-white text-gray-700 rounded-tl-none shadow-sm border border-gray-100"
                        }`}
                      >
                        {msg.content}
                        <div
                          className={`text-[10px] mt-1 text-right ${
                            isMe ? "text-green-100" : "text-gray-400"
                          }`}
                        >
                          {new Date(msg.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <div className="p-3 bg-white border-t border-gray-100 flex items-center gap-2 pb-6">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                placeholder="Type a message..."
                className="flex-1 bg-gray-100 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-green-400 text-gray-700"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim()}
                className="bg-[#53B552] text-white p-3 rounded-xl hover:bg-green-600 disabled:opacity-50 transition-colors shadow-sm"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        )}

        {/* --- HEADER CHÍNH --- */}
        <div className="bg-[#E3F1E4] px-6 pb-6 pt-8 rounded-b-[40px] shadow-sm shrink-0 z-10">
          <div className="flex items-center justify-between mb-4">
            <Link href="/user_page/main_page">
              <button className="bg-white p-2 rounded-full shadow-sm hover:bg-green-50 transition">
                <ArrowLeft size={20} className="text-green-700" />
              </button>
            </Link>
            <h1
              className={`${jost.className} text-2xl font-bold text-green-800`}
            >
              Connections
            </h1>
            <div className="w-10"></div>
          </div>

          <div className="relative flex flex-col gap-1">
            <div className="relative w-full">
              <input
                type="number"
                placeholder="Enter User ID..."
                value={inputFriendId}
                onChange={(e) => setInputFriendId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendRequest()}
                className={`${jost.className} w-full pl-10 pr-12 py-3 rounded-2xl border-none shadow-md outline-none`}
              />
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                size={18}
              />
              <button
                onClick={handleSendRequest}
                disabled={addLoading || !inputFriendId}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-[#53B552] p-1.5 rounded-xl text-white hover:bg-green-600 disabled:opacity-50"
              >
                {addLoading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <UserPlus size={18} />
                )}
              </button>
            </div>
            <div className="h-5 pl-2">
              {feedback && (
                <span
                  className={`text-xs font-bold ${
                    feedback.type === "success"
                      ? "text-green-600"
                      : "text-red-500"
                  } flex items-center gap-1`}
                >
                  {feedback.text}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* --- TABS --- */}
        <div className="px-6 mt-2 flex gap-4 border-b border-gray-200 shrink-0 overflow-x-auto no-scrollbar">
          {/* Code Tab Friends/Requests/Sent cũ của bạn (giữ nguyên logic hiển thị activeTab) */}
          <button
            onClick={() => setActiveTab("friends")}
            className={`pb-2 text-sm font-bold ${
              activeTab === "friends"
                ? "text-[#53B552] border-b-2 border-[#53B552]"
                : "text-gray-400"
            }`}
          >
            Friends{" "}
            <span className="ml-1 bg-green-100 text-green-700 px-2 rounded-full text-xs">
              {friends.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab("requests")}
            className={`pb-2 text-sm font-bold ${
              activeTab === "requests"
                ? "text-[#53B552] border-b-2 border-[#53B552]"
                : "text-gray-400"
            }`}
          >
            Requests{" "}
            {requests.length > 0 && (
              <span className="ml-1 bg-red-100 text-red-600 px-2 rounded-full text-xs">
                {requests.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("sent")}
            className={`pb-2 text-sm font-bold ${
              activeTab === "sent"
                ? "text-[#53B552] border-b-2 border-[#53B552]"
                : "text-gray-400"
            }`}
          >
            Sent{" "}
            {sentRequests.length > 0 && (
              <span className="ml-1 bg-gray-100 text-gray-600 px-2 rounded-full text-xs">
                {sentRequests.length}
              </span>
            )}
          </button>
        </div>

        {/* --- MAIN CONTENT --- */}
        <main className="flex-1 overflow-y-auto p-4 pb-20">
          {loading ? (
            <div className="flex justify-center mt-10">
              <Loader2 className="animate-spin text-green-600" size={32} />
            </div>
          ) : (
            <div className="space-y-3">
              {/* TAB FRIENDS - CẬP NHẬT NÚT CHAT */}
              {activeTab === "friends" &&
                (friends.length === 0 ? (
                  <p className="text-center text-gray-400 mt-10">
                    No friends yet.
                  </p>
                ) : (
                  friends.map((item) => {
                    const displayId = getDisplayId(item);
                    return (
                      <div
                        key={item.friend_id + "_" + item.user_id}
                        className="bg-white p-3 rounded-2xl shadow-sm flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-full bg-gray-100 relative overflow-hidden">
                            <Image
                              src="/images/default-avatar.png"
                              alt="User"
                              fill
                              className="object-cover"
                            />
                          </div>
                          <div>
                            <h3
                              className={`${jost.className} font-bold text-gray-800`}
                            >
                              User ID: {displayId}
                            </h3>
                            <p className="text-xs text-green-600">Connected</p>
                          </div>
                        </div>

                        {/* BUTTONS: CHAT & UNFRIEND */}
                        <div className="flex gap-2">
                          {/* Nút Chat Mới */}
                          <button
                            onClick={() => openChat(item)}
                            className="p-2 bg-green-50 text-green-600 rounded-full hover:bg-green-100 transition"
                          >
                            <MessageCircle size={20} />
                          </button>
                          {/* Nút Xóa bạn */}
                          <button
                            onClick={() => handleUnfriendClick(displayId)}
                            className="p-2 bg-red-50 text-red-400 rounded-full hover:bg-red-100 transition"
                          >
                            <UserMinus size={20} />
                          </button>
                        </div>
                      </div>
                    );
                  })
                ))}

              {/* TAB REQUESTS (GIỮ NGUYÊN) */}
              {activeTab === "requests" &&
                (requests.length === 0 ? (
                  <p className="text-center text-gray-400 mt-10">
                    No requests.
                  </p>
                ) : (
                  requests.map((req) => (
                    <div
                      key={req.friend_id}
                      className="bg-white p-3 rounded-2xl shadow-sm flex items-center justify-between"
                    >
                      {/* ... UI Request cũ ... */}
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-gray-100 relative overflow-hidden">
                          <Image
                            src="/images/default-avatar.png"
                            alt="User"
                            fill
                            className="object-cover"
                          />
                        </div>
                        <div>
                          <h3
                            className={`${jost.className} font-bold text-gray-800`}
                          >
                            User ID: {req.friend_id}
                          </h3>
                          <p className="text-xs text-gray-400">Requesting...</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAccept(req.friend_id)}
                          className="bg-[#53B552] text-white p-2 rounded-full"
                        >
                          <Check size={18} />
                        </button>
                        <button
                          onClick={() => handleReject(req.friend_id)}
                          className="bg-white text-red-400 border p-2 rounded-full"
                        >
                          <X size={18} />
                        </button>
                      </div>
                    </div>
                  ))
                ))}

              {/* TAB SENT (GIỮ NGUYÊN) */}
              {activeTab === "sent" &&
                (sentRequests.length === 0 ? (
                  <p className="text-center text-gray-400 mt-10">
                    No sent requests.
                  </p>
                ) : (
                  sentRequests.map((req) => (
                    <div
                      key={req.friend_id}
                      className="bg-white p-3 rounded-2xl shadow-sm flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-gray-100 relative overflow-hidden">
                          <Image
                            src="/images/default-avatar.png"
                            alt="User"
                            fill
                            className="object-cover"
                          />
                        </div>
                        <div>
                          <h3
                            className={`${jost.className} font-bold text-gray-800`}
                          >
                            User ID: {req.friend_id}
                          </h3>
                          <p className="text-xs text-orange-400">Waiting...</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleCancelRequest(req.friend_id)}
                        className="px-4 py-2 bg-gray-100 text-gray-500 text-xs font-bold rounded-xl"
                      >
                        Cancel
                      </button>
                    </div>
                  ))
                ))}
            </div>
          )}
        </main>

        {/* --- FOOTER (Giữ nguyên) --- */}
        <footer className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20">
          {/* Copy lại footer cũ của bạn */}
          <div className="h-1 bg-linear-to-r from-transparent via-green-200 to-transparent"></div>
          <div className="flex justify-around items-center py-3">
            {/* ... Các link Home, Planning, Ecobot ... */}
            <Link
              href="/homepage"
              className="flex flex-col items-center text-gray-400 hover:text-green-600"
            >
              <Home size={24} />
              <span className="text-xs">Home</span>
            </Link>
            <Link
              href="/planning_page/showing_plan_page"
              className="flex flex-col items-center text-gray-400 hover:text-green-600"
            >
              <MapPin size={24} />
              <span className="text-xs">Planning</span>
            </Link>
            <Link
              href="#"
              className="flex flex-col items-center text-gray-400 hover:text-green-600"
            >
              <Bot size={24} />
              <span className="text-xs">Ecobot</span>
            </Link>
            <div className="flex flex-col items-center text-[#53B552]">
              <Link href="/user_page/main_page">
                <User size={24} strokeWidth={2.5} />
                <span className="text-xs font-bold mt-1">User</span>
              </Link>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
