import AuthForm from "@/components/AuthForm";

export default function AdminLoginPage() {
  return (
    <main className="content-page auth-page">
      <AuthForm mode="admin" />
    </main>
  );
}

