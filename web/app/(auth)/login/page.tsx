import SectionCard from "../../../components/ui/section-card";

export default function LoginPage() {
  return (
    <main>
      <h1>Login</h1>
      <SectionCard
        title="Auth Scaffold"
        description="The UI shell exists, but real registration and session handling are still planned."
      >
        <p>Next step: connect this page to the future `/api/v1/auth/login` workflow.</p>
      </SectionCard>
    </main>
  );
}
