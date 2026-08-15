import { redirect } from "next/navigation";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { ChatWindow } from "@/components/ChatWindow";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Chat — Clinexa",
  description: "Ask questions about your health reports. Get AI-powered, citation-backed answers.",
};

export default async function ChatPage() {
  let session = null;

  try {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
    if (url && key && !url.includes("placeholder")) {
      const cookieStore = cookies();
      const supabase = createServerClient(url, key, {
        cookies: { get: (name) => cookieStore.get(name)?.value }
      });
      const { data } = await supabase.auth.getSession();
      session = data?.session ?? null;
    }
  } catch (err) {
    session = null;
  }

  if (!session) redirect("/login");

  return (
    <div className="h-full flex flex-col">
      <div className="px-8 py-6 border-b border-surface-border flex-shrink-0">
        <h1 className="section-title">AI Health Assistant</h1>
        <p className="section-subtitle">Ask questions about your lab results. Answers are grounded in your uploaded reports.</p>
      </div>
      <div className="flex-1 overflow-hidden">
        <ChatWindow />
      </div>
    </div>
  );
}
