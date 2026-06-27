"use client";
import { useParams } from "next/navigation";
import useSWR from "swr";
import { useState } from "react";

type ChallengeDetail = {
title: string;
description: string; // markdown
hints: string[];
endpoint: string;    // URL to the isolated container
};

export default function ChallengeDetail() {
const { category, slug } = useParams() as { category: string; slug: string };
const { data } = useSWR<ChallengeDetail>(`/api/v1/challenges/${slug}`);
const [flag, setFlag] = useState("");
const [msg, setMsg] = useState("");

const submitFlag = async () => {
    const res = await fetch("/api/v1/solves", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ challenge_slug: slug, flag }),
    });
    const result = await res.json();
    setMsg(result.message);
};

if (!data) return <p>Loading…</p>;

return (
    <section className="p-8 text-neonGreen">
    <h1 className="text-3xl font-greekRune mb-4">{data.title}</h1>
    <article className="prose prose-invert max-w-none mb-6"
                dangerouslySetInnerHTML={{ __html: data.description }} />
    <div className="mb-4">
        <h2 className="font-greekRune">Hints</h2>
        <ul className="list-disc ml-6">
        {data.hints.map((h, i) => (
            <li key={i} dangerouslySetInnerHTML={{ __html: h }} />
        ))}
        </ul>
    </div>

    <div className="bg-obsidian p-4 rounded mb-4">
        <p>Target endpoint (interact from your browser or curl):</p>
        <code className="block break-all">{data.endpoint}</code>
    </div>

    <div className="flex gap-2">
        <input
        type="text"
        placeholder="Enter flag"
        className="flex-1 p-2 rounded bg-gray-800 text-neonGreen"
        value={flag}
        onChange={(e) => setFlag(e.target.value)}
        />
        <button
        onClick={submitFlag}
        className="px-4 py-2 bg-neonGreen text-obsidian font-bold rounded hover:bg-glitchRed transition"
        >
        Submit
        </button>
    </div>
    {msg && <p className="mt-2">{msg}</p>}
    </section>
);
}
