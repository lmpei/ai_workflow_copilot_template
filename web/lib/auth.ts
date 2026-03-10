export type AuthRoutes = {
  login: string;
  register: string;
};

export function getAuthRoutes(): AuthRoutes {
  return {
    login: "/login",
    register: "/register",
  };
}

export function isAuthImplemented(): boolean {
  return false;
}
