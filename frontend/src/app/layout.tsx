import type { Metadata, Viewport } from "next";
import { Inter, Geist } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { AuthProvider } from "@/providers/auth-context";
import { Toaster } from "@/components/ui/sonner";
import { cn } from "@/lib/utils";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "AutoWorth AI — AI-Powered Vehicle Valuation",
    template: "%s | AutoWorth AI",
  },
  description:
    "India's most intelligent AI-powered used car valuation platform. Get accurate, transparent, and explainable vehicle pricing through machine learning and computer vision.",
  keywords: [
    "used car valuation",
    "car price prediction",
    "AI car valuation",
    "vehicle price estimator",
    "India used cars",
  ],
  authors: [{ name: "AutoWorth AI" }],
  openGraph: {
    title: "AutoWorth AI — AI-Powered Vehicle Valuation",
    description:
      "Accurate, transparent, and explainable used car pricing powered by ML and Computer Vision.",
    type: "website",
    locale: "en_IN",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0f" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={cn(
        "h-full antialiased",
        inter.variable,
        geist.variable,
        "font-sans"
      )}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <QueryProvider>
          <AuthProvider>
            {children}
            <Toaster richColors position="top-right" />
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
