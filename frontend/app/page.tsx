import { redirect } from "next/navigation";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export default async function Home() {
  let session = null;

  try {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

    if (url && key && !url.includes("placeholder")) {
      const cookieStore = cookies();
      const supabase = createServerClient(url, key, {
        cookies: {
          get(name: string) {
            return cookieStore.get(name)?.value;
          },
        },
      });
      const { data } = await supabase.auth.getSession();
      session = data?.session ?? null;
    }
  } catch (err) {
    session = null;
  }

  if (session) {
    redirect("/dashboard");
  } else {
    redirect("/login");
  }
}
