"use client";
import {
  Knewave,
  Josefin_Sans,
  Abhaya_Libre,
  Poppins,
  Gotu,
  Jost,
} from "next/font/google";
import { Home, MapPin, Bot, User } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Heart, Bookmark } from "lucide-react"; // Đã xóa Star vì chưa dùng

export const gotu = Gotu({
  subsets: ["latin"],
  weight: ["400"],
});
export const jost = Jost({
  subsets: ["latin"],
  weight: ["700"],
});
export const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["700"],
});

export const poppins = Poppins({
  subsets: ["latin"],
  weight: ["300"],
});
export const josefin_sans = Josefin_Sans({
  subsets: ["latin"],
  weight: ["700"],
});

export const knewave = Knewave({
  subsets: ["latin"],
  weight: ["400"],
});

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [heart, setHeart] = useState(false);
  const [bookMark, setBookMark] = useState(false);
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault(); // Chặn việc tải lại trang mặc định

    // Nếu có từ khóa thì mới chuyển trang
    if (searchQuery.trim()) {
      // Chuyển sang trang map kèm theo từ khóa trên URL
      // Ví dụ: /map_page?q=Green%20Coffee
      router.push(`/map_page?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      // Nếu rỗng thì cứ chuyển qua map mặc định
      router.push("/map_page");
    }
  };

  const handleSearchNearby = () => {
    router.push("/map_page?nearby=true");
  };

  return (
    // 1. WRAPPER NGOÀI CÙNG (Màu xám, căn giữa)
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      {/* 2. KHUNG APP (Giới hạn chiều rộng max-w-md ~ 450px) */}
      <div className="w-full max-w-md bg-gray-50 h-screen flex flex-col overflow-hidden shadow-2xl relative">
        <header className="bg-[#53B552] px-4 pt-5 pb-6 shadow-md shrink-0 z-10">
          <form
            onSubmit={handleSearchSubmit}
            className={`flex justify-between items-center gap-4`}
          >
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
              <input
                type="text"
                className={`${abhaya_libre.className} w-full rounded-full py-2 pl-10 pr-3 text-sm
              bg-white text-black focus:outline-none focus:ring-2 focus:ring-green-300 placeholder:text-green-700 placeholder:font-semibold`}
                placeholder="Search for an eco-friendly place"
                value={searchQuery}
                onChange={handleChange}
              />
            </div>
            <div
              className={`${knewave.className} text-white font-bold text-2xl select-none`}
            >
              EcomoveX
            </div>
          </form>
          <div className="flex justify-center gap-3 mt-4 flex-wrap">
            {["Café", "Restaurant", "Park", "Hotel", "Shopping"].map((i) => (
              <button
                key={i}
                className={`${jost.className} cursor-pointer bg-white text-[#53B552] rounded-full px-4 py-1 text-sm font-medium hover:text-white hover:bg-green-500`}
              >
                {i}
              </button>
            ))}
          </div>
        </header>

        <main
          className={`p-4 flex-1 overflow-y-auto flex flex-col gap-5 pb-20`}
        >
          <section
            className={`bg-[#F9FFF9] rounded-xl shadow-sm p-4 border border-green-100`}
          >
            <h2
              className={`${jost.className} font-bold text-green-600 uppercase mb-3 text-xl tracking-wide`}
            >
              Most Visited Green Places
            </h2>
            <div className="relative w-full h-48 rounded-lg overflow-hidden">
              <Image
                src="/images/tao-dan-park.png"
                alt="Tao Dan Park"
                layout="fill"
                objectFit="cover"
              />
            </div>
            <div className="flex gap-2 justify-between items-center mt-3">
              <div className="flex gap-3">
                <Heart
                  className={`${
                    heart
                      ? "fill-green-600 stroke-green-600 scale-110"
                      : "stroke-green-600"
                  } cursor-pointer transition-all size-6 text-green-600 strokeWidth={1.5} hover:fill-green-600 `}
                  onClick={() => setHeart(!heart)}
                />
                <Bookmark
                  onClick={() => setBookMark(!bookMark)}
                  className={`${
                    bookMark
                      ? "fill-green-600 stroke-green-600 scale-110"
                      : "stroke-green-600"
                  } cursor-pointer transition-all size-6 text-green-600 strokeWidth={1.5} hover:fill-green-600 `}
                />
              </div>
              <div className="text-right">
                <p
                  className={`${abhaya_libre.className} font-semibold text-gray-800`}
                >
                  Tao Dan Park
                </p>
                <p
                  className={`${abhaya_libre.className} text-sm text-gray-500`}
                >
                  2km
                </p>
              </div>
            </div>
            <div className="flex justify-center gap-2 mt-4">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <div className="w-2 h-2 rounded-full bg-gray-200"></div>
              <div className="w-2 h-2 rounded-full bg-gray-200"></div>
              <div className="w-2 h-2 rounded-full bg-gray-200"></div>
              <div className="w-2 h-2 rounded-full bg-gray-200"></div>
              <div className="w-2 h-2 rounded-full bg-gray-200"></div>
            </div>
          </section>

          <section className={`grid grid-cols-2 gap-4`}>
            <div className="bg-linear-to-b from-green-500 to-green-50 rounded-xl p-4 text-black flex flex-col shadow-lg min-h-[150px]">
              {/* Nội dung Your last trip */}
            </div>

            <div className="bg-linear-to-b from-green-50 to-green-400 rounded-xl p-4 shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center">
              <h3
                className={`${abhaya_libre.className} text-green-700 font-semibold text-xl uppercase leading-tight`}
              >
                Nearby Eco-Friendly Spots
              </h3>
              <button
                onClick={handleSearchNearby}
                className={`${jost.className} bg-green-600 text-white rounded-full px-5 py-2 text-sm font-semibold mt-4 hover:text-green-500 hover:bg-white cursor-pointer`}
              >
                Search Now
              </button>
            </div>
          </section>

          <section className="bg-[#E9F5EB] rounded-2xl p-6 shadow-sm mt-4">
            <h3
              className={`${josefin_sans.className} text-[#5BB95B] text-2xl font-bold leading-tight mb-3`}
            >
              Explore Local Green Activities
            </h3>

            <p
              className={`${abhaya_libre.className} text-gray-700 text-lg leading-relaxed`}
            >
              Discover eco-friendly experiences near you and make every trip
              meaningful.
            </p>

            <div className="flex justify-end mt-5">
              <button
                className={`${jost.className} border-[3px] border-[#6BC86A] text-[#5BB95B] bg-transparent rounded-full px-10 py-1.5 text-lg font-bold hover:bg-[#5BB95B] hover:text-white hover:border-[#5BB95B] transition-all duration-300 shadow-sm`}
              >
                Explore
              </button>
            </div>
          </section>
        </main>

        <footer
          className={`bg-white shadow-[0_-2px_6px_rgba(0,0,0,0.05)] ${poppins.className} shrink-0 z-10`}
        >
          <div className="h-0.5 bg-linear-to-r from-transparent via-green-300 to-transparent opacity-70"></div>
          <div className="flex justify-around items-center px-2 pt-2 pb-3">
            <Link
              href="/homepage"
              className="flex flex-col items-center justify-center w-1/4 text-green-600"
            >
              <Home className="size-6 select-none" strokeWidth={2.0} />
              <span className="text-xs font-medium mt-0.5">Home</span>
            </Link>

            <Link
              href="/planning_page/showing_plan_page"
              className="flex flex-col items-center justify-center w-1/4 text-gray-400"
            >
              <MapPin
                className="size-6 text-gray-400 cursor-pointer transition-all duration-200 hover:text-green-600 hover:scale-110"
                strokeWidth={1.5}
              />
              <span className="text-xs font-medium mt-0.5">Planning</span>
            </Link>

            <Link
              href="#"
              className="flex flex-col items-center justify-center w-1/4 text-gray-400"
            >
              <Bot
                className="size-6 text-gray-400 cursor-pointer transition-all duration-200 hover:text-green-600 hover:scale-110"
                strokeWidth={1.5}
              />
              <span className="text-xs font-medium mt-0.5">Ecobot</span>
            </Link>

            <Link
              href="user_page/main_page"
              className="flex flex-col items-center justify-center w-1/4 text-gray-400"
            >
              <User
                className="size-6 text-gray-400 cursor-pointer transition-all duration-200 hover:text-green-600 hover:scale-110"
                strokeWidth={1.5}
              />
              <span className="text-xs font-medium mt-0.5">User</span>
            </Link>
          </div>
        </footer>
      </div>
    </div>
  );
}
