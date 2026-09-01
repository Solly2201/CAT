import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { LoginInput, LoginResponse, PublicUser, RegisterInput, RegisterResponse } from "@cap/contracts";
import { api, setUnauthorizedHandler } from "../lib/api";
import { clearToken, readToken, writeRefreshToken, writeToken } from "../lib/auth-storage";

// Frontend auth state for the bearer-token API.
//
// The JWT is the only persisted state; the user is always re-fetched from
// GET /auth/me on load rather than cached beside it, so a revoked token
// cannot leave a stale "signed in" shell on screen.
//
// The API issues a 15-minute access token plus a 7-day refresh token.
// The response interceptor renews the pair transparently on a 401; only
// when refresh itself fails (expiry, revocation) does the session end and
// the user return to the login screen.

export type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  user: PublicUser | null;
  status: AuthStatus;
  /** True when the last session ended because the API rejected its token,
   *  not because the user logged out. Cleared on the next sign-in. */
  sessionExpired: boolean;
  login: (input: LoginInput) => Promise<PublicUser>;
  register: (input: RegisterInput) => Promise<RegisterResponse>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<PublicUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>(() => (readToken() ? "loading" : "anonymous"));
  const [sessionExpired, setSessionExpired] = useState(false);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setStatus("anonymous");
    setSessionExpired(false);
  }, []);

  useEffect(() => {
    // The interceptor fires only once a presented token was rejected AND
    // refresh could not renew it — i.e. the session genuinely ended
    // (expiry or revocation), as opposed to a failed login. That is worth
    // saying out loud on the login screen rather than letting it look
    // like a fresh visit.
    setUnauthorizedHandler(() => {
      setUser(null);
      setStatus("anonymous");
      setSessionExpired(true);
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  useEffect(() => {
    if (!readToken()) return;
    let active = true;

    api
      .get<{ user: PublicUser }>("/auth/me")
      .then((response) => {
        if (!active) return;
        setUser(response.data.user);
        setStatus("authenticated");
      })
      .catch(() => {
        // Either way we cannot prove who the user is: present as anonymous.
        if (!active) return;
        setUser(null);
        setStatus("anonymous");
      });

    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (input: LoginInput) => {
    const response = await api.post<LoginResponse>("/auth/login", input);
    writeToken(response.data.token);
    if (response.data.refreshToken) writeRefreshToken(response.data.refreshToken);
    setUser(response.data.user);
    setStatus("authenticated");
    setSessionExpired(false);
    return response.data.user;
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    // No sign-in here: the API needs a verified address before it issues
    // a token.
    const response = await api.post<RegisterResponse>("/auth/register", input);
    return response.data;
  }, []);

  const value = useMemo(
    () => ({ user, status, sessionExpired, login, register, logout }),
    [user, status, sessionExpired, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside an AuthProvider.");
  return context;
}
