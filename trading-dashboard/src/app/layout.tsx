import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Trading Dashboard - Advanced Crypto Bot",
  description: "Real-time cryptocurrency trading bot dashboard with analytics, portfolio management, and automated strategies.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider
          defaultTheme="system"
          storageKey="trading-dashboard-theme"
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
