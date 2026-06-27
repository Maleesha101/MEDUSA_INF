
"use client";
import useSWR from "swr";
import { useEffect, useState } from "react";
import { io } from "socket.io-client";

type Challenge = {
slug: string;
title: string;
category: string;
difficulty: string;
};

export default function Dashboard() {
const { data: challenges } = useSWR<Challenge[]>("/api/v1/challenges");
const [score, setScore] = useState(0);
const [rank, setRank] = useState(0);

// WebSocket live updates
useEffect(() => {
    const socket = io("/", { path: "/ws/scoreboard" });
    socket.on("score_update", (msg: any) => {
    if (msg.team_id === "my-team-id") {
        setScore((prev) => prev + msg.points);
    }
    });
    return () => socket.disconnect();
}, []);

return (
    <section className="p-8 text-neonGreen">
    <h2 className="text-2xl font-greekRune mb-4">Team Dashboard</h2>
    <div className="mb-6">
        <p className="text-xl">Score: {score}</p>
        <p className="text-sm">Rank: #{rank}</p>
    </div>

    <h3 className="font-greekRune text-xl mb-2">Available Challenges</h3>
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {challenges?.map((c) => (
        <a
            key={c.slug}
            href={`/challenges/${c.category}/${c.slug}`}
            className="border border-neonGreen p-4 rounded hover:bg-gray-800 transition"
        >
            <h4 className="font-bold">{c.title}</h4>
            <p>{c.category} • {c.difficulty}</p>
        </a>
        ))}
    </div>
    </section>
);
}

