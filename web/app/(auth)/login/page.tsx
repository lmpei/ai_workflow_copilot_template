import LoginForm from "../../../components/auth/login-form";
import { getPublicDemoSettings } from "../../../lib/api";

export default async function LoginPage() {
  const publicDemoResponse = await getPublicDemoSettings();
  const publicDemoSettings =
    publicDemoResponse && "public_demo_mode" in publicDemoResponse ? publicDemoResponse : null;

  return (
    <main>
      <h1>登录</h1>
      <LoginForm publicDemoSettings={publicDemoSettings} />
    </main>
  );
}
