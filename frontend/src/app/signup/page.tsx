"use client";
import {Knewave, Josefin_Sans, Abhaya_Libre, Poppins } from "next/font/google";
import {useState} from 'react';
import Link from "next/link";
import {gotu} from "../page";
import { FaEnvelope } from "react-icons/fa";
const knewave = Knewave({
  subsets: ["latin"],
  weight: ["400"],
});

export  const poppins = Poppins({
  subsets: ["latin"],
  weight: ["300"]
});
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["700"],
});

const josefin_sans = Josefin_Sans({
  subsets: ["latin"],
  weight: ["700"],
});



export default function SignupPage(){
    const [form, setForm] = useState({
      username : "",
      password: "",
      authorize: "",
      email: "",
    });
    const [passwordError, setPasswordError] = useState("");

    const handleChange = (e : React.ChangeEvent<HTMLInputElement>) => {
      const { name, value } = e.target;
      setForm(prev => ({
        ...prev,
        [name]: value
      }));
      
      if (name === 'password') {
        setPasswordError("");
        if (form.authorize && value !== form.authorize) {
          setPasswordError("Passwords do not match");
        }
      }

      // Check password match when authorize field changes
      if (name === 'authorize') {
        if (value !== form.password) {
          setPasswordError("Passwords do not match");
        } else {
          setPasswordError("");
        }
      }
    };

    const handleSubmit = (e : React.FormEvent) =>{
        e.preventDefault();
        alert(`Welcome ${form.username}`);
    }

    return (
        <div className="flex flex-col min-h-screen items-center justify-center bg-white">
            <main className="flex min-h-screen w-full max-w-md flex-col items-center justify-center
            py-8 px-4 bg-white dark:bg-black
            sm:max-w-3xl sm:py-24 sm:px-16 sm:items-start sm:justify-center">
                <h1 className={`${knewave.className} text-6xl text-green-600 mb-4 text-center translate-x-40 -translate-y-10`}>
                  Ecomove<span className="text-green-500">X</span>
                </h1>

                <p className={`${josefin_sans.className} text-green-600 mb-12 text-center text-xl leading-relaxed translate-x-42 -translate-y-10`}>
                  Your Trip. Your impact. Your choice.
                </p>
                <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-sm -translate-y-10">
                <input 
                type = "text"
                name = "username"
                value = {form.username}
                onChange={handleChange}
                placeholder = "Enter your username"
                className={`${abhaya_libre.className} w-full border-2 bg-green-100 text-green-700 rounded-full px-5 py-3 text-lg font-medium translate-x-30`}
                required
                />
                <input
                type = "text"
                value = {form.email}
                onChange = {handleChange}
                placeholder="Enter your email"
                name = "email"
                className={`${abhaya_libre.className} w-full border-2 bg-green-100 text-green-700 rounded-full px-5 py-3 text-lg font-medium translate-x-30`}
                required
                />
                  <input 
                  type = "password"
                  value = {form.password}
                  name = "password"
                  onChange = {handleChange}
                  placeholder="Enter your password"
                  className={`${abhaya_libre.className} w-full border-2 bg-green-100 text-green-700 rounded-full px-5 py-3 text-lg font-medium translate-x-30`}
                  required
                  />
                <div className="w-full">
                  <input 
                  type = "password"
                  value = {form.authorize}
                  name = "authorize"
                  onChange = {handleChange}
                  placeholder="Authorize your password"
                  className={`${abhaya_libre.className} w-full border-2 ${
                    passwordError 
                      ? 'border-red-500 bg-red-50' 
                      : 'bg-green-100'
                  } text-green-700 rounded-full px-5 py-3 text-lg font-medium translate-x-30`}
                  required
                  disabled={!form.password}
                  />
                  {passwordError && (
                    <p className="text-red-500 text-sm translate-x-50 mt-1 ml-4">{passwordError}</p>
                  )}
                </div>
                <button
                disabled={!!passwordError || !form.password || !form.authorize}
                type="submit"
                className={`${abhaya_libre.className} w-full bg-green-500 text-white rounded-full py-3 text-lg font-medium hover:bg-green-600 translate-x-30 transition`}
                >Sign up</button>
                </form>
                <p className={`${gotu.className} text-green-500 mb-12 text-center text-xl leading-relaxed translate-x-42 -translate-y+30`}>Have an account? 
                  <Link 
                  href="../login"
                  className={`${josefin_sans.className} text-green-600 mb-12 text-center text-xl leading-relaxed translate-x-42 -translate-y-10 hover:text-green-700`}>
                  Login</Link>
                </p>
            </main> 
        </div>
    );
}