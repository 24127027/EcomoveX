"use client";
import {useState} from 'react'
import {poppins, knewave, abhaya_libre, josefin_sans, gotu} from "../../page";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { FaRegEnvelope } from "react-icons/fa";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function SigninPage() {
    const [form, setForm] = useState({
      username : "",
      password: "",
      email: "",
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();

    const handleSubmit = async (e : React.FormEvent)=>{
            e.preventDefault();
            setLoading(true);
            setError("");

            try {
                const response = await api.login({
                    email: form.email,
                    password: form.password
                });

                // Store token
                localStorage.setItem('access_token', response.access_token);
                localStorage.setItem('user_id', response.user_id.toString());
                
                // Redirect to dashboard or home
                router.push('/dashboard');
            } catch (err: any) {
                setError(err.message || "Login failed. Please try again.");
            } finally {
                setLoading(false);
            }
    };
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm({
        ...form,
        [e.target.name]: e.target.value  // ← This uses the 'name' attribute
      });
    };

    const [showPassword, setShowPassword] = useState(false);
    return (
        
        <div className="flex flex-col min-h-screen items-center justify-center bg-white">
            <main className="flex min-h-screen w-full max-w-md flex-col items-center justify-center
            py-8 px-4 bg-white dark:bg-black
            sm:max-w-3xl sm:py-24 sm:px-16 sm:items-start sm:justify-center">
                <h1 className={`${knewave.className} text-6xl text-green-600 mb-4 text-center translate-x-40 -translate-y-40`}>
                  Ecomove<span className="text-green-500">X</span>
                </h1>

                <p className={`${josefin_sans.className} text-green-600 mb-12 text-center text-xl leading-relaxed translate-x-42 -translate-y-40`}>
                  Your Trip. Your impact. Your choice.
                </p>
                <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-sm -translate-y-40">
                
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
                type="email"
                name="email"  // ← Make sure this says "email"
                value={form.email}
                onChange={handleChange}
                placeholder="Enter your email"
                className={`${abhaya_libre.className} w-full border-2 bg-green-100 text-green-700 rounded-full px-5 py-3 text-lg font-medium translate-x-30`}
                required
                />
                <div className = "relative w-full">
                <input 
                type = {showPassword ? "text" : "password" }
                value = {form.password}
                name = "password"
                onChange = {handleChange}
                placeholder="Enter your password"
                className={`${abhaya_libre.className} w-full border-2 bg-green-100 text-green-700 rounded-full px-5 py-3 text-lg font-medium translate-x-30`}
                required
                />
                <button type = "button"
                onClick = {()=>setShowPassword(!showPassword)}
                className = "absolute inset-y-0 mb-2 translate-x-115 translate-y-1 flex items-center text-green-700 hover:text-green-900">
                    {showPassword ? <EyeOff size={22}/> : <Eye size={22}/>}
                </button>
                </div>
                <Link
                href="../forget_Password"
                className = {`${abhaya_libre.className}  w-full text-lg text-green-500 translate-x-90 hover:text-green-800`}>Forgot Password?</Link>
                <button
                type="submit"
                className={`${abhaya_libre.className} w-full bg-green-500 text-white rounded-full py-3 text-lg font-medium hover:bg-green-600 translate-x-30 transition`}
                >Login</button>
                </form>
                <p className={`${gotu.className} text-green-500 mb-12 text-center text-xl leading-relaxed translate-x-42 -translate-y-30`}>Not a member? 
                  <Link 
                  href="../signup"
                  className={`${josefin_sans.className} text-green-600 mb-12 text-center text-xl leading-relaxed translate-x-42 hover:text-green-700 -translate-y-10`}>
                  Sign up</Link>
                </p>
            </main> 
        </div>
    )
};