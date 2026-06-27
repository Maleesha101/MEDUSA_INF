import { useEffect, useState } from "react";

interface TeamScore {
team_id: string;
display_name: string;
score: number;
}

export default function Scoreboard() {
const [board, setBoard] = useState<TeamScore[]>([]);

useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/scoreboard`);
    ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "leaderboard") setBoard(data.data);
    };
    ws.onclose = () => console.warn("Scoreboard WS closed");
    return () => ws.close();
}, []);

return (
    <section className="max-w-4xl mx-auto">
    <h1 className="text-3xl font-bold text-green-400 mb-6">Live Scoreboard</h1>
    <table className="w-full text-left">
        <thead className="bg-gray-800">
        <tr>
            <th className="px-4 py-2">#</th>
            <th className="px-4 py-2">Team</th>
            <th className="px-4 py-2">Score</th>
        </tr>
        </thead>
        <tbody>
        {board.map((t, i) => (
            <tr
            key={t.team_id}
            className={i % 2 ? "bg-gray-900" : "bg-gray-800"}
            >
            <td className="px-4 py-2">{i + 1}</td>
            <td className="px-4 py-2">{t.display_name}</td>
            <td className="px-4 py-2">{t.score}</td>
            </tr>
        ))}
        </tbody>
    </table>
    </section>
);
}
