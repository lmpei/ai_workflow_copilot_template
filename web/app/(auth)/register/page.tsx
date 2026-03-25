import RegisterForm from "../../../components/auth/register-form";
import { getPublicDemoSettings } from "../../../lib/api";

export default async function RegisterPage() {
  const publicDemoResponse = await getPublicDemoSettings();
  const publicDemoSettings =
    publicDemoResponse && "public_demo_mode" in publicDemoResponse ? publicDemoResponse : null;

  return (
    <main>
      <h1>Register</h1>
      <RegisterForm publicDemoSettings={publicDemoSettings} />
    </main>
  );
}
