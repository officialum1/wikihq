import AuthForm from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <main className="content-page auth-page">
      <AuthForm mode="login" />
    </main>
  );
}

