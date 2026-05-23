"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { Shield, Lock, KeyRound, AlertCircle, CheckCircle2, ArrowLeft } from "lucide-react";

type AuthMode = "login" | "register";

export function AuthForm() {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [registeredData, setRegisteredData] = useState<{
    id: number;
    name: string;
    email: string;
    public_key_pem: string;
  } | null>(null);

  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      await login(email, password);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesion");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setSuccess("");

    if (password !== confirmPassword) {
      setError("Las contrasenas no coinciden");
      setIsLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("La contrasena debe tener al menos 8 caracteres");
      setIsLoading(false);
      return;
    }

    try {
      const data = await api.register({ name, email, password });
      setRegisteredData(data);
      setSuccess(`Usuario registrado correctamente. ID: ${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrar");
    } finally {
      setIsLoading(false);
    }
  };

  const switchToLogin = () => {
    setMode("login");
    setError("");
    setSuccess("");
    setRegisteredData(null);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-primary/10 rounded-xl border border-primary/20">
              <Shield className="h-8 w-8 text-primary" />
            </div>
            <h1 className="text-3xl font-bold text-foreground">VaultChain</h1>
          </div>
          <p className="text-muted-foreground">
            Sistema de Mensajeria Segura con Registro Inmutable
          </p>
        </div>

        {/* Auth Card */}
        <div className="bg-card border border-border rounded-2xl p-6 shadow-xl">
          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => {
                setMode("login");
                setError("");
                setSuccess("");
                setRegisteredData(null);
              }}
              className={`flex-1 py-2.5 px-4 rounded-xl text-sm font-medium transition-all ${
                mode === "login"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              Iniciar Sesion
            </button>
            <button
              onClick={() => {
                setMode("register");
                setError("");
                setSuccess("");
              }}
              className={`flex-1 py-2.5 px-4 rounded-xl text-sm font-medium transition-all ${
                mode === "register"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              Registrarse
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-destructive/10 border border-destructive/30 rounded-xl flex items-center gap-2 text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="mb-4 p-3 bg-success/10 border border-success/30 rounded-xl flex items-center gap-2 text-success">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span className="text-sm">{success}</span>
            </div>
          )}

          {/* Registration Success Details */}
          {registeredData && (
            <div className="mb-4 p-4 bg-secondary rounded-xl space-y-3">
              <h3 className="font-semibold text-foreground flex items-center gap-2">
                <KeyRound className="h-4 w-4 text-primary" />
                Registro Exitoso
              </h3>
              <div className="text-sm space-y-1 text-muted-foreground">
                <p><span className="text-foreground">Nombre:</span> {registeredData.name}</p>
                <p><span className="text-foreground">Email:</span> {registeredData.email}</p>
                <p><span className="text-foreground">ID:</span> {registeredData.id}</p>
              </div>
              <details className="text-sm">
                <summary className="cursor-pointer text-primary hover:underline">
                  Ver llave publica ECDSA
                </summary>
                <pre className="mt-2 p-2 bg-background rounded-lg text-xs overflow-x-auto text-muted-foreground">
                  {registeredData.public_key_pem}
                </pre>
              </details>
              <p className="text-xs text-muted-foreground">
                Tu llave privada fue cifrada con PBKDF2-HMAC-SHA256.
              </p>
              <Button onClick={switchToLogin} className="w-full mt-2" variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Ir a Iniciar Sesion
              </Button>
            </div>
          )}

          {/* Login Form */}
          {mode === "login" && (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">
                  Correo electronico
                </label>
                <Input
                  type="email"
                  placeholder="usuario@ejemplo.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-input border-border"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">
                  Contrasena
                </label>
                <Input
                  type="password"
                  placeholder="********"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-input border-border"
                />
              </div>
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <div className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                    Validando...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Lock className="h-4 w-4" />
                    Iniciar Sesion
                  </span>
                )}
              </Button>
            </form>
          )}

          {/* Register Form */}
          {mode === "register" && !registeredData && (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">
                  Nombre completo
                </label>
                <Input
                  type="text"
                  placeholder="Juan Perez"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="bg-input border-border"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">
                  Correo electronico
                </label>
                <Input
                  type="email"
                  placeholder="usuario@ejemplo.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-input border-border"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">
                  Contrasena
                </label>
                <Input
                  type="password"
                  placeholder="Minimo 8 caracteres"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-input border-border"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">
                  Confirmar contrasena
                </label>
                <Input
                  type="password"
                  placeholder="Repite tu contrasena"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="bg-input border-border"
                />
              </div>
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <div className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                    Generando llaves ECDSA...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <KeyRound className="h-4 w-4" />
                    Crear Cuenta
                  </span>
                )}
              </Button>
              <p className="text-xs text-center text-muted-foreground">
                Al registrarte se generara automaticamente tu par de llaves ECDSA
                para firmar digitalmente tus mensajes.
              </p>
            </form>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          Cifrado AES-256-GCM + Firma ECDSA + Blockchain
        </p>
      </div>
    </div>
  );
}
