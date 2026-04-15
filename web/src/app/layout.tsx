import type { Metadata } from "next";
import { Inter, Noto_Sans_KR } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const notoSansKR = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-noto",
});

export const metadata: Metadata = {
  title: "지식 베이스",
  description: "Local AI-powered knowledge base",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" className={`${inter.variable} ${notoSansKR.variable}`} data-theme="dark">
      {/* Inline script: apply saved theme before first paint to prevent flash */}
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('kb-theme');if(t)document.documentElement.setAttribute('data-theme',t);}catch(e){}})();`,
          }}
        />
      </head>
      <body
        style={{
          fontFamily: "var(--font-noto), var(--font-inter), -apple-system, sans-serif",
        }}
      >
        {children}
      </body>
    </html>
  );
}
