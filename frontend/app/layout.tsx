  import "./globals.css";
  import { Inter } from "next/font/google";
  import { ThemeProvider } from "@/components/ThemeProvider";

  const inter = Inter({ subsets: ["latin"] });

  export const metadata = {
    title: "MEDUSA – Capture The Flag",
    description: "Greek‑mythology themed CTF platform",
  };

  export default function RootLayout({
    children,
  }: {
    children: React.ReactNode;
  }) {
    return (
      <html lang="en" className="dark">
        <body className={`${inter.className} bg-[#0b0b0b] text-[#00ff7f]`}>
          <ThemeProvider>{children}</ThemeProvider>
        </body>
      </html>
    );
  }
