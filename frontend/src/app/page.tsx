import {
  Knewave,
  Josefin_Sans,
  Abhaya_Libre,
  Poppins,
  Gotu,
} from "next/font/google";
import Link from "next/link";

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

const metadata = {
  title: "EcomoveX",
  description: "Discover the new green destination",
  type: "website",
};
export default function FirstPage() {
  return (
    <div className="flex flex-col min-h-screen items-center justify-center bg-white">
      <main
        className="
  flex min-h-screen w-full max-w-md flex-col items-center justify-center
  py-8 px-4 bg-white dark:bg-black
  sm:max-w-3xl sm:py-24 sm:px-16 sm:items-start sm:justify-center"
      >
        <h1
          className={`${knewave.className} items-center text-6xl text-green-600 mb-4 text-center `}
        >
          Ecomove<span className="text-green-500">X</span>
        </h1>

        <p
          className={`${josefin_sans.className} text-green-600 mb-12 text-center text-xl leading-relaxed`}
        >
          Your Trip. Your impact. Your choice.
        </p>

        <div className="flex flex-col w-full gap-4">
          <Link
            href="/signup"
            className={`${abhaya_libre.className} w-full text-center border-2 border-green-500 text-green-500 rounded-full py-3 text-lg font-medium hover:bg-green-100 transition`}
          >
            Sign up
          </Link>

          <Link
            href="/login"
            className={`${abhaya_libre.className} w-full text-center bg-green-500 border-green-500 text-white rounded-full py-3 text-lg font-medium hover:bg-green-600 transition`}
          >
            Sign in
          </Link>
        </div>
      </main>
    </div>
  );
}
