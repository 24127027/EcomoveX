import {
  Knewave,
  Josefin_Sans,
  Abhaya_Libre,
  Poppins,
  Gotu,
} from "next/font/google";
import Link from "next/link";
import { Search } from "lucide-react";
export const gotu = Gotu({
  subsets: ["latin"],
  weight: ["400"],
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
  const handleChange = () => {};
  return (
    <div
      className={`bg-green-600 p-4 flex justify-between items-center relative`}
    >
      <div>
        <Search className="absolute left-2 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
        <input
          type="text"
          className={`${abhaya_libre} border absolute rounded-full py-2 pl-9 pr-2 text-sm`}
          placeholder="Search for an eco-friendly place"
          onChange={handleChange}
        />
      </div>
    </div>
  );
}
