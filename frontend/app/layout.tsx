import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";

import "./globals.css";

const googleLike = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-ui",
  weight: ["400", "500", "600", "700"],
});


export const metadata: Metadata = {
  title: "agent.gift",
  description: "Profil odaklı hediye araştırma ve öneri deneyimi.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr">
      <body className={`${googleLike.variable} font-sans`}>
        {children}
      </body>
    </html>
  );
}
