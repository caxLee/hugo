import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI News",
  description: "最新的AI技术新闻和资讯",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={`${inter.className} antialiased`}>
        <div className="min-h-screen bg-white">
          {/* Header */}
          <header className="border-b border-gray-100">
            <div className="max-w-4xl mx-auto px-4 py-6">
              <div className="flex items-center justify-center">
                <h1 className="text-2xl font-bold text-gray-900">
                  AI News
                </h1>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="max-w-4xl mx-auto px-4 py-8">
            {children}
          </main>

          {/* Footer */}
          <footer className="border-t border-gray-100 mt-16">
            <div className="max-w-4xl mx-auto px-4 py-8">
              <div className="flex items-center justify-center text-sm text-gray-500">
                <span>© 2025 AI News</span>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
