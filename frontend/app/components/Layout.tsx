import React from "react";
import Navbar from "./Navbar";

export default function Layout({ children }: { children: React.ReactNode }) {
return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-mono">
    <Navbar />
    <main className="container mx-auto py-8 px-4">{children}</main>
    </div>
);
}
