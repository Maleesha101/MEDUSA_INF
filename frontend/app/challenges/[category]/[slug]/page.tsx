import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import axios from "axios";

export default function ChallengeDetail() {
const router = useRouter();
const { slug } = router.query as { slug: string };
const [challenge, setChallenge] = useState<any>(null);
const [flag, setFlag] = useState("");
const [msg, setMsg] = useState("");

useEffect(() => {
    if (!slug) return;
    axios
    .get(`/api/v1/challenges/${slug}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("access")}` },
    })
    .then((r) => setChallenge(r.data))
    .catch(() => setMsg("Failed to load challenge"));
}, [slug]);

const submitFlag = async () => {
    try {
    const res = await axios.post(
        "/api/v1/solves/",
        { slug, flag },
        { headers: { Authorization: `Bearer ${localStorage.getItem("access")}` } }
    );
    setMsg(res.data.message);
    } catch (e: any) {
    setMsg(e.response?.data?.detail || "Error submitting flag");
    }
};

if (!challenge) return <p>Loading…</p>;

return (
    <section className="max-w-3xl mx-auto">
    <h1 className="text-3xl font-bold text-green-400">{challenge.title}</h1>
    <p className="mt-4 text-gray-300">{challenge.description}</p>

    <div className="mt-6 p-4 bg-gray-800 rounded">
        <h2 className="text-xl font-semibold text-green-300 mb-2">Endpoint</h2>
        <code className="block text-sm text-green-200">{challenge.endpoint}</code>
        <p className="mt-2 text-sm text-gray-400">
        Connect to the endpoint using the provided port; each team gets a
        unique DNS name.
        </p>
    </div>

    <div className="mt-6">
        <input
        type="text"
        placeholder="Enter flag"
        value={flag}
        onChange={(e) => setFlag(e.target.value)}
        className="w-full p-2 rounded bg-gray-700 text-gray-100"
        />
        <button
        onClick={submitFlag}
        className="mt-2 w-full bg-green-600 hover:bg-green-500 py-2 rounded"
        >
        Submit Flag
        </button>
    </div>

    {msg && <p className="mt-4 text-green-300">{msg}</p>}
    </section>
);
}

