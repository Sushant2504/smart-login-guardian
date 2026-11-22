import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smart Login Guardian - Security Dashboard",
  description: "Enterprise Identity Threat Detection Platform with 3D Visualization",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
