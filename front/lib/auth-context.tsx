"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { api, User, LoginResult } from "@/lib/api";

// ---------------------------------------------------------------------------
// Tipos
// ---------------------------------------------------------------------------

export type MfaLoginChallenge = {
  mfaRequired: true;
  mfaSessionToken: string;
};

export type LoginOutcome =
  | { mfaRequired: false }
  | MfaLoginChallenge;

interface AuthContextType {
  user: User | null;
  token: string | null;
  password: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  /** Primer factor. Devuelve mfaRequired=true si se necesita código TOTP. */
  login: (email: string, password: string) => Promise<LoginOutcome>;
  /** Segundo factor: verifica OTP y completa el login. */
  completeMfaLogin: (mfaSessionToken: string, otpCode: string, password: string) => Promise<void>;
  logout: () => void;
  setUserData: (user: User) => void;
}

// ---------------------------------------------------------------------------
// Contexto
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [password, setPassword] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("vaultchain_token");
    const savedUser = localStorage.getItem("vaultchain_user");
    const savedPassword = localStorage.getItem("vaultchain_password");

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      setPassword(savedPassword);
      api.setToken(savedToken);
    }
    setIsLoading(false);
  }, []);

  // ---- helpers internos ----

  const _finalizeLogin = async (accessToken: string, email: string, pwd: string) => {
    setToken(accessToken);
    setPassword(pwd);
    api.setToken(accessToken);

    localStorage.setItem("vaultchain_token", accessToken);
    localStorage.setItem("vaultchain_password", pwd);

    const users = await api.getUsers();
    const currentUser = users.find((u: User) => u.email === email);
    if (currentUser) {
      setUser(currentUser);
      localStorage.setItem("vaultchain_user", JSON.stringify(currentUser));
    }
  };

  // ---- login (primer factor) ----

  const login = async (email: string, pwd: string): Promise<LoginOutcome> => {
    const result: LoginResult = await api.login(email, pwd);

    if (!result.mfa_required) {
      // Sin MFA → login completo
      await _finalizeLogin(result.access_token!, email, pwd);
      return { mfaRequired: false };
    }

    // Con MFA → devolver el token de sesión para que el componente pida el OTP
    return {
      mfaRequired: true,
      mfaSessionToken: result.mfa_session_token!,
    };
  };

  // ---- completeMfaLogin (segundo factor) ----

  const completeMfaLogin = async (
    mfaSessionToken: string,
    otpCode: string,
    pwd: string,
  ) => {
    const result: LoginResult = await api.verifyMfa(mfaSessionToken, otpCode);
    // Necesitamos el email del payload del token de sesión MFA
    const payloadB64 = mfaSessionToken.split(".")[1];
    const payload = JSON.parse(atob(payloadB64));
    await _finalizeLogin(result.access_token!, payload.email as string, pwd);
  };

  // ---- logout ----

  const logout = () => {
    setToken(null);
    setUser(null);
    setPassword(null);
    api.setToken(null);
    localStorage.removeItem("vaultchain_token");
    localStorage.removeItem("vaultchain_user");
    localStorage.removeItem("vaultchain_password");
  };

  const setUserData = (userData: User) => {
    setUser(userData);
    localStorage.setItem("vaultchain_user", JSON.stringify(userData));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-primary">Cargando...</div>
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        password,
        isAuthenticated: !!token,
        isLoading,
        login,
        completeMfaLogin,
        logout,
        setUserData,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}
