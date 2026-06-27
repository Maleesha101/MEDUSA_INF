import { motion } from "framer-motion";

export default function Home() {
return (
    <section className="flex flex-col items-center justify-center min-h-[70vh] text-center">
    <motion.img
        src="/assets/snake.svg"
        alt="Medusa snake"
        className="w-48 mb-8 filter drop-shadow-[0_0_10px_#00ff00]"
        animate={{ rotate: [0, -10, 10, -10, 0] }}
        transition={{ repeat: Infinity, duration: 6 }}
    />
    <h1 className="text-5xl font-extrabold text-green-400 mb-4">
        Welcome to MEDUSA CTF
    </h1>
    <p className="text-lg text-gray-300 max-w-2xl">
        A Greek‑mythology‑themed Capture‑the‑Flag platform with intentionally
        vulnerable challenge containers. Register, join a team, and start
        hunting flags!
    </p>
    <div className="mt-8">
        <a
        href="/register"
        className="px-6 py-3 bg-green-600 rounded hover:bg-green-500 transition"
        >
        Get Started
        </a>
    </div>
    </section>
);
}
