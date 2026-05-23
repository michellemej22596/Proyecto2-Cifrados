"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { api, User } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  password: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setUserData: (user: User) => void;
}

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

  const login = async (email: string, pwd: string) => {
    const data = await api.login(email, pwd);
    const accessToken = data.access_token;
    
    setToken(accessToken);
    setPassword(pwd);
    api.setToken(accessToken);
    
    localStorage.setItem("vaultchain_token", accessToken);
    localStorage.setItem("vaultchain_password", pwd);
    
    // Fetch user info from users list
    const users = await api.getUsers();
    const currentUser = users.find((u: User) => u.email === email);
    if (currentUser) {
      setUser(currentUser);
      localStorage.setItem("vaultchain_user", JSON.stringify(currentUser));
    }
  };

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
        login,
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
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
