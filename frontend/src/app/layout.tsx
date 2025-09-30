import type { Metadata } from "next";
import { GeistSans, GeistMono } from "geist/font";
import { ParticlesBackground } from "@/components/ui/ParticlesBackground";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentR - AI Web Research Assistant",
  description: "Your AI co-pilot for web research.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="bg-gradient-to-b from-zinc-900 to-black text-white antialiased">
        {children}
      </body>
    </html>
  );
}