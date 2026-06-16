import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import AdminDashboard from "@/components/AdminDashboard";

export default function AdminPage() {
  const token = cookies().get("token");
  if (!token?.value) {
    redirect("/admin/login");
  }

  return (
    <main className="content-page wide">
      <AdminDashboard />
    </main>
  );
}

