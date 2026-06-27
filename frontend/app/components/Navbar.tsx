
import Link from "next/link";
import { useRouter } from "next/router";

export default function Navbar() {
const { pathname } = useRouter();
const links = [
    { href: "/", label: "Home" },
    { href: "/challenges", label: "Challenges" },
    { href: "/scoreboard", label: "Scoreboard" },
    { href: "/dashboard", label: "Dashboard" },
    { href: "/admin", label: "Admin", admin: true },
];

return (
    <nav className="bg-gray-800 border-b border-gray-700">
    <div className="container mx-auto flex items-center justify-between py-3">
        <div className="text-2xl font-bold text-green-400">MEDUSA</div>
        <ul className="flex space-x-4">
        {links.map((l) => (
            <li key={l.href}>
            <Link href={l.href}>
                <a
                className={`px-3 py-1 rounded ${
                    pathname === l.href ? "bg-green-600" : "hover:bg-gray-700"
                }`}
                >
                {l.label}
                </a>
            </Link>
            </li>
        ))}
        </ul>
    </div>
    </nav>
);
}
