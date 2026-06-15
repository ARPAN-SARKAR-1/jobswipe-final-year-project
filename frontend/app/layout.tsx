import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";

import Footer from "@/components/Footer";
import Navbar from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Swipe for Success",
  description: "Swipe for Success is a swipe-based job discovery and recruitment platform.",
  icons: {
    apple: "/swipe-for-success-logo.png",
    icon: "/swipe-for-success-logo.png"
  }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        {children}
        <Footer />
        <Toaster position="top-right" toastOptions={{ duration: 3200 }} />
      </body>
    </html>
  );
}
