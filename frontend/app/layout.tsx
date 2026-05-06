import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";

import Footer from "@/components/Footer";
import Navbar from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "JobSwipe",
  description: "Swipe-based job and internship discovery for freshers and job seekers."
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
