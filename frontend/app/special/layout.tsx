import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

export default function SpecialLayout({ children }: { children: ReactNode }) {
  const token = cookies().get("token");
  if (!token?.value) {
    redirect("/auth/login");
  }
  return <>{children}</>;
}
