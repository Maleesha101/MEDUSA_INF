"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
const [email, setEmail] = useState("");
const [password, setPassword] = useState("");
const router = useRouter();

const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    });
    if (res.ok) {
    const data = await res.json();
    // store tokens in httpOnly cookie via Set‑Cookie header (handled by FastAPI)
    router.push("/dashboard");
    } else {
    alert("Login failed");
    }
};

return (
    <section className="flex min-h-screen items-center justify-center">
     <form
        className="bg-obsidian p-8 rounded-lg shadow-lg animate-snake"
        onSubmit={handleSubmit}
    >
        <h1 className="text-3xl mb-6 font-greekRune text-neonGreen text-center">
        MEDUSA CTF – Login
        </h1>
        <input
        type="email"
        placeholder="Email"
        className="w-full p-2 mb-4 rounded bg-gray-800 text-neonGreen"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        />
        <input
        type="password"
        placeholder="Password"
        className="w-full p-2 mb-6 rounded bg-gray-800 text-neonGreen"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        />
        <button
        type="submit"
        className="w-full py-2 bg-neonGreen text-obsidian font-bold rounded hover:bg-glitchRed transition"
        >
        Enter the Labyrinth
        </button>
     </form>
    </section>
);
}
