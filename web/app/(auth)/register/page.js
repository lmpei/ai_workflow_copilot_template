import SectionCard from "../../../components/ui/section-card";

export default function RegisterPage() {
  return (
    <main>
      <h1>Register</h1>
      <SectionCard
        title="Account Creation"
        description="This route reserves the user onboarding flow in the App Router structure."
      >
        <p>Next step: add form state, validation, and a real auth provider.</p>
      </SectionCard>
    </main>
  );
}
