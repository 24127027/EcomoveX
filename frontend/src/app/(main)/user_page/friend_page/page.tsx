"use client";

import React, { useEffect, useState } from "react";
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
  Send, // Import thêm icon Send
} from "lucide-react";
import { Jost, Abhaya_Libre } from "next/font/google";
import { api, FriendResponse } from "@/lib/api"; //

const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "700"] });
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "700", "800"],
});

export default function FriendsPage() {
  // 1. Thêm "sent" vào kiểu dữ liệu tab
  const [activeTab, setActiveTab] = useState<"friends" | "requests" | "sent">(
    "friends"
  );

  const [friends, setFriends] = useState<FriendResponse[]>([]);
  const [requests, setRequests] = useState<FriendResponse[]>([]);
  const [sentRequests, setSentRequests] = useState<FriendResponse[]>([]); // State cho danh sách đã gửi

  const [loading, setLoading] = useState(true);
  const [inputFriendId, setInputFriendId] = useState("");
  const [addLoading, setAddLoading] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);

  // State thông báo (Feedback)
  const [feedback, setFeedback] = useState<{
    text: string;
    type: "success" | "error";
  } | null>(null);

  // State quản lý Modal xóa bạn
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const currentUser = await api.getUserProfile(); //
      if (currentUser) setCurrentUserId(currentUser.id);

      // 2. Gọi API lấy danh sách Sent
      const [friendsData, requestsData, sentData] = await Promise.all([
        api.getFriends(), //
        api.getPendingRequests(), //
        api.getSentRequests(), //
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

  // --- HÀM XỬ LÝ GỬI KẾT BẠN ---
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
    try {
      setAddLoading(true);
      await api.sendFriendRequest(idToSend); //
      setFeedback({
        text: "Friend request sent successfully",
        type: "success",
      });
      setInputFriendId("");
      fetchData(); // Load lại data để cập nhật tab Sent
    } catch (error: any) {
      const msg = error.message?.toLowerCase() || "";
      if (msg.includes("not found") || msg.includes("404")) {
        setFeedback({
          text: "ID doesn't exist. Please try again",
          type: "error",
        });
      } else if (msg.includes("yourself")) {
        setFeedback({ text: "You cannot add yourself", type: "error" });
      } else if (msg.includes("already exists") || msg.includes("friendship")) {
        setFeedback({
          text: "Already friends or request pending",
          type: "error",
        });
      } else {
        setFeedback({ text: "Failed to send request", type: "error" });
      }
    } finally {
      setAddLoading(false);
    }
  };

  // --- CÁC HÀM XỬ LÝ KHÁC ---
  const handleAccept = async (friendId: number) => {
    try {
      await api.acceptFriendRequest(friendId); //
      setFeedback({ text: "Friend request accepted!", type: "success" });
      fetchData();
    } catch (e) {
      setFeedback({ text: "Failed to accept request", type: "error" });
    }
  };

  const handleReject = async (friendId: number) => {
    try {
      await api.rejectFriendRequest(friendId); //
      setFeedback({ text: "Request declined", type: "success" });
      fetchData();
    } catch (e) {
      setFeedback({ text: "Failed to decline request", type: "error" });
    }
  };

  // --- HÀM MỚI: HỦY LỜI MỜI ĐÃ GỬI ---
  const handleCancelRequest = async (friendId: number) => {
    try {
      // Dùng chung endpoint unfriend để xóa record friendship
      await api.unfriend(friendId); //
      setFeedback({ text: "Request cancelled", type: "success" });
      fetchData();
    } catch (e) {
      setFeedback({ text: "Failed to cancel request", type: "error" });
    }
  };

  // --- LOGIC XÓA BẠN (MODAL) ---
  const handleUnfriendClick = (friendId: number) => {
    setFeedback(null);
    setDeleteTargetId(friendId);
  };

  const confirmDeleteFriend = async () => {
    if (!deleteTargetId) return;
    try {
      await api.unfriend(deleteTargetId); //
      setFeedback({ text: "Friend removed successfully", type: "success" });
      fetchData();
    } catch (e) {
      setFeedback({ text: "Failed to remove friend", type: "error" });
    } finally {
      setDeleteTargetId(null);
    }
  };

  const getDisplayId = (item: FriendResponse) => {
    if (!currentUserId) return item.friend_id;
    return item.user_id === currentUserId ? item.friend_id : item.user_id;
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* --- CUSTOM MODAL (Xác nhận xóa bạn) --- */}
        {deleteTargetId && (
          <div className="absolute inset-0 bg-black/60 z-50 flex items-center justify-center p-6 animate-in fade-in duration-200">
            <div className="bg-white rounded-3xl p-6 w-full max-w-sm shadow-2xl transform transition-all scale-100 animate-in zoom-in-95">
              <div className="flex flex-col items-center text-center">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4 text-red-500">
                  <AlertTriangle size={24} />
                </div>
                <h3
                  className={`${jost.className} text-xl font-bold text-gray-800 mb-2`}
                >
                  Unfriend User?
                </h3>
                <p className="text-gray-500 text-sm mb-6">
                  Are you sure you want to remove{" "}
                  <span className="font-bold text-gray-700">
                    ID: {deleteTargetId}
                  </span>{" "}
                  from your friends list? This action cannot be undone.
                </p>
                <div className="flex gap-3 w-full">
                  <button
                    onClick={() => setDeleteTargetId(null)}
                    className="flex-1 py-3 rounded-xl bg-gray-100 text-gray-700 font-bold hover:bg-gray-200 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmDeleteFriend}
                    className="flex-1 py-3 rounded-xl bg-red-500 text-white font-bold hover:bg-red-600 shadow-md shadow-red-200 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- HEADER --- */}
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

          {/* --- INPUT SEARCH --- */}
          <div className="relative flex flex-col gap-1">
            <div className="relative w-full">
              <input
                type="number"
                placeholder="Enter User ID (e.g., 5)..."
                value={inputFriendId}
                onChange={(e) => {
                  setInputFriendId(e.target.value);
                  if (feedback) setFeedback(null);
                }}
                onKeyDown={(e) => e.key === "Enter" && handleSendRequest()}
                className={`${jost.className} w-full pl-10 pr-12 py-3 rounded-2xl border-none shadow-md focus:ring-2 focus:ring-green-400 outline-none text-gray-700 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none`}
              />
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                size={18}
              />
              <button
                onClick={handleSendRequest}
                disabled={addLoading || !inputFriendId}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-[#53B552] p-1.5 rounded-xl text-white shadow-sm hover:bg-green-600 disabled:opacity-50 transition-colors"
              >
                {addLoading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <UserPlus size={18} />
                )}
              </button>
            </div>

            {/* --- FEEDBACK MESSAGE --- */}
            <div className="h-5 pl-2">
              {feedback && (
                <span
                  className={`text-xs font-bold ${
                    feedback.type === "success"
                      ? "text-green-600"
                      : "text-red-500"
                  } flex items-center gap-1 animate-in slide-in-from-top-1`}
                >
                  {feedback.type === "success" ? (
                    <Check size={14} strokeWidth={3} />
                  ) : (
                    <X size={14} strokeWidth={3} />
                  )}
                  {feedback.text}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* --- TABS --- */}
        <div className="px-6 mt-2 flex gap-4 border-b border-gray-200 shrink-0 overflow-x-auto no-scrollbar">
          {/* TAB: Friends */}
          <button
            onClick={() => setActiveTab("friends")}
            className={`pb-2 text-sm font-bold transition-all whitespace-nowrap ${
              activeTab === "friends"
                ? "text-[#53B552] border-b-2 border-[#53B552]"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            My Friends{" "}
            <span className="ml-1 bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs">
              {friends.length}
            </span>
          </button>

          {/* TAB: Requests */}
          <button
            onClick={() => setActiveTab("requests")}
            className={`pb-2 text-sm font-bold transition-all whitespace-nowrap ${
              activeTab === "requests"
                ? "text-[#53B552] border-b-2 border-[#53B552]"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            Requests{" "}
            {requests.length > 0 && (
              <span className="ml-1 bg-red-100 text-red-600 px-2 py-0.5 rounded-full text-xs">
                {requests.length}
              </span>
            )}
          </button>

          {/* TAB: Sent (MỚI) */}
          <button
            onClick={() => setActiveTab("sent")}
            className={`pb-2 text-sm font-bold transition-all whitespace-nowrap ${
              activeTab === "sent"
                ? "text-[#53B552] border-b-2 border-[#53B552]"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            Sent{" "}
            {sentRequests.length > 0 && (
              <span className="ml-1 bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                {sentRequests.length}
              </span>
            )}
          </button>
        </div>

        {/* --- MAIN CONTENT --- */}
        <main className="flex-1 overflow-y-auto p-4 pb-20">
          {loading ? (
            <div className="flex justify-center mt-10 text-green-600">
              <Loader2 className="animate-spin" size={32} />
            </div>
          ) : (
            <div className="space-y-3">
              {/* ---------------- TAB FRIENDS ---------------- */}
              {activeTab === "friends" &&
                (friends.length === 0 ? (
                  <div className="text-center mt-10 opacity-50">
                    <Users size={48} className="mx-auto text-gray-300 mb-2" />
                    <p className="text-gray-500">No friends yet.</p>
                  </div>
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
                        <button
                          onClick={() => handleUnfriendClick(displayId)}
                          className="p-2 text-red-400 hover:bg-red-50 rounded-full transition-colors"
                        >
                          <UserMinus size={20} />
                        </button>
                      </div>
                    );
                  })
                ))}

              {/* ---------------- TAB REQUESTS ---------------- */}
              {activeTab === "requests" &&
                (requests.length === 0 ? (
                  <div className="text-center mt-10 opacity-50">
                    <User size={48} className="mx-auto text-gray-300 mb-2" />
                    <p className="text-gray-500">No pending requests.</p>
                  </div>
                ) : (
                  requests.map((req) => (
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
                          <p className="text-xs text-gray-400">
                            Sent a request
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAccept(req.friend_id)}
                          className="bg-[#53B552] text-white p-2 rounded-full hover:bg-green-600"
                        >
                          <Check size={18} />
                        </button>
                        <button
                          onClick={() => handleReject(req.friend_id)}
                          className="bg-white text-red-400 border p-2 rounded-full hover:bg-red-50"
                        >
                          <X size={18} />
                        </button>
                      </div>
                    </div>
                  ))
                ))}

              {/* ---------------- TAB SENT (MỚI) ---------------- */}
              {activeTab === "sent" &&
                (sentRequests.length === 0 ? (
                  <div className="text-center mt-10 opacity-50">
                    <Send size={48} className="mx-auto text-gray-300 mb-2" />
                    <p className="text-gray-500">No sent requests.</p>
                  </div>
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
                          <p className="text-xs text-orange-400">
                            Waiting for response...
                          </p>
                        </div>
                      </div>
                      {/* Nút Hủy lời mời trực tiếp */}
                      <button
                        onClick={() => handleCancelRequest(req.friend_id)}
                        className="px-4 py-2 bg-gray-100 text-gray-500 text-xs font-bold rounded-xl hover:bg-gray-200 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  ))
                ))}
            </div>
          )}
        </main>

        {/* --- FOOTER --- */}
        <footer className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20">
          <div className="h-1 bg-linear-to-r from-transparent via-green-200 to-transparent"></div>
          <div className="flex justify-around items-center py-3">
            <Link
              href="/homepage"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <Home size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Home
              </span>
            </Link>
            <Link
              href="/planning_page/showing_plan_page"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <MapPin size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Planning
              </span>
            </Link>
            <Link
              href="#"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <Bot size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Ecobot
              </span>
            </Link>
            <div className="flex flex-col items-center text-[#53B552] relative cursor-pointer">
              <div className="relative">
                <Link href="/user_page/main_page">
                  <User size={24} strokeWidth={2.5} />
                  {requests.length > 0 && (
                    <span className="absolute -top-1.5 -right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white shadow-xs animate-in zoom-in">
                      {requests.length > 9 ? "9+" : requests.length}
                    </span>
                  )}
                </Link>
              </div>

              <span className={`${jost.className} text-xs font-bold mt-1`}>
                User
              </span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
