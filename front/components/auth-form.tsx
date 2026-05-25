"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { 
  Shield, 
  Lock, 
  KeyRound, 
  AlertCircle, 
  CheckCircle2, 
  ArrowLeft, 
  Mail, 
  User, 
  Eye, 
  EyeOff,
  Sparkles,
  ShieldCheck,
  Fingerprint,
  Link2
} from "lucide-react";

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
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
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

  const features = [
    { icon: ShieldCheck, text: "Cifrado AES-256-GCM", color: "text-cyan-400" },
    { icon: Fingerprint, text: "Firma ECDSA", color: "text-emerald-400" },
    { icon: Link2, text: "Blockchain Inmutable", color: "text-violet-400" },
  ];

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-background to-background" />
        <div className="absolute top-20 -left-20 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-20 w-80 h-80 bg-primary/5 rounded-full blur-3xl animate-pulse delay-1000" />
        
        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center p-12 xl:p-20">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-4 bg-primary/10 rounded-2xl border border-primary/20 backdrop-blur-sm">
              <Shield className="h-12 w-12 text-primary" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-foreground">VaultChain</h1>
              <p className="text-muted-foreground">Mensajeria Segura</p>
            </div>
          </div>

          <h2 className="text-3xl xl:text-4xl font-bold text-foreground mb-4 leading-tight">
            Comunicacion privada,<br />
            <span className="text-primary">verificable y segura</span>
          </h2>

          <p className="text-lg text-muted-foreground mb-12 max-w-md">
            Protege tus conversaciones con cifrado de extremo a extremo y registro 
            inmutable en blockchain.
          </p>

          {/* Features */}
          <div className="space-y-4">
            {features.map((feature, i) => (
              <div 
                key={i}
                className="flex items-center gap-4 p-4 bg-card/50 rounded-xl border border-border/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 cursor-default"
              >
                <div className={`p-2.5 rounded-lg bg-background/50 ${feature.color}`}>
                  <feature.icon className="h-5 w-5" />
                </div>
                <span className="font-medium text-foreground">{feature.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="p-3 bg-primary/10 rounded-xl border border-primary/20">
                <Shield className="h-8 w-8 text-primary" />
              </div>
              <h1 className="text-3xl font-bold text-foreground">VaultChain</h1>
            </div>
            <p className="text-muted-foreground">
              Sistema de Mensajeria Segura
            </p>
          </div>

          {/* Auth Card */}
          <div className="bg-card border border-border rounded-2xl p-6 lg:p-8 shadow-xl shadow-black/5">
            {/* Tabs */}
            <div className="flex gap-2 mb-6 p-1 bg-secondary/50 rounded-xl">
              <button
                onClick={() => {
                  setMode("login");
                  setError("");
                  setSuccess("");
                  setRegisteredData(null);
                }}
                className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-300 ${
                  mode === "login"
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                    : "text-muted-foreground hover:text-foreground"
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
                className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-300 ${
                  mode === "register"
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Registrarse
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-destructive/10 border border-destructive/30 rounded-xl flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
                <span className="text-sm text-destructive">{error}</span>
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="mb-6 p-4 bg-success/10 border border-success/30 rounded-xl flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
                <span className="text-sm text-success">{success}</span>
              </div>
            )}

            {/* Registration Success Details */}
            {registeredData && (
              <div className="mb-6 p-5 bg-gradient-to-br from-success/10 to-primary/5 rounded-xl border border-success/20 space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-success" />
                  Registro Exitoso
                </h3>
                <div className="text-sm space-y-2 text-muted-foreground">
                  <p className="flex items-center gap-2">
                    <User className="h-4 w-4 text-primary" />
                    <span className="text-foreground">{registeredData.name}</span>
                  </p>
                  <p className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-primary" />
                    <span className="text-foreground">{registeredData.email}</span>
                  </p>
                </div>
                <details className="text-sm group">
                  <summary className="cursor-pointer text-primary hover:text-primary/80 flex items-center gap-2 transition-colors">
                    <KeyRound className="h-4 w-4" />
                    Ver llave publica ECDSA
                  </summary>
                  <pre className="mt-3 p-3 bg-background/50 rounded-lg text-xs overflow-x-auto text-muted-foreground border border-border">
                    {registeredData.public_key_pem}
                  </pre>
                </details>
                <p className="text-xs text-muted-foreground flex items-center gap-2">
                  <Lock className="h-3 w-3" />
                  Tu llave privada fue cifrada con PBKDF2-HMAC-SHA256
                </p>
                <Button onClick={switchToLogin} className="w-full mt-2 gap-2" variant="outline">
                  <ArrowLeft className="h-4 w-4" />
                  Ir a Iniciar Sesion
                </Button>
              </div>
            )}

            {/* Login Form */}
            {mode === "login" && (
              <form onSubmit={handleLogin} className="space-y-5">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    Correo electronico
                  </label>
                  <Input
                    type="email"
                    placeholder="usuario@ejemplo.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="h-12 bg-input border-border focus:ring-2 focus:ring-primary/20 transition-all"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Lock className="h-4 w-4 text-muted-foreground" />
                    Contrasena
                  </label>
                  <div className="relative">
                    <Input
                      type={showPassword ? "text" : "password"}
                      placeholder="********"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="h-12 bg-input border-border pr-12 focus:ring-2 focus:ring-primary/20 transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>
                <Button 
                  type="submit" 
                  className="w-full h-12 text-base font-medium shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all" 
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <span className="flex items-center gap-2">
                      <div className="h-5 w-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                      Validando...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Lock className="h-5 w-5" />
                      Iniciar Sesion
                    </span>
                  )}
                </Button>
              </form>
            )}

            {/* Register Form */}
            {mode === "register" && !registeredData && (
              <form onSubmit={handleRegister} className="space-y-5">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    Nombre completo
                  </label>
                  <Input
                    type="text"
                    placeholder="Juan Perez"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="h-12 bg-input border-border focus:ring-2 focus:ring-primary/20 transition-all"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    Correo electronico
                  </label>
                  <Input
                    type="email"
                    placeholder="usuario@ejemplo.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="h-12 bg-input border-border focus:ring-2 focus:ring-primary/20 transition-all"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Lock className="h-4 w-4 text-muted-foreground" />
                    Contrasena
                  </label>
                  <div className="relative">
                    <Input
                      type={showPassword ? "text" : "password"}
                      placeholder="Minimo 8 caracteres"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="h-12 bg-input border-border pr-12 focus:ring-2 focus:ring-primary/20 transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Lock className="h-4 w-4 text-muted-foreground" />
                    Confirmar contrasena
                  </label>
                  <div className="relative">
                    <Input
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Repite tu contrasena"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      className="h-12 bg-input border-border pr-12 focus:ring-2 focus:ring-primary/20 transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
                    >
                      {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>
                <Button 
                  type="submit" 
                  className="w-full h-12 text-base font-medium shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all" 
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <span className="flex items-center gap-2">
                      <div className="h-5 w-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                      Generando llaves ECDSA...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <KeyRound className="h-5 w-5" />
                      Crear Cuenta
                    </span>
                  )}
                </Button>
                <p className="text-xs text-center text-muted-foreground leading-relaxed">
                  Al registrarte se generara automaticamente tu par de llaves ECDSA
                  para firmar digitalmente tus mensajes.
                </p>
              </form>
            )}
          </div>

          {/* Mobile Features */}
          <div className="lg:hidden mt-8 flex justify-center gap-6">
            {features.map((feature, i) => (
              <div key={i} className="flex flex-col items-center gap-2">
                <div className={`p-2 rounded-lg bg-card/50 border border-border ${feature.color}`}>
                  <feature.icon className="h-4 w-4" />
                </div>
                <span className="text-xs text-muted-foreground">{feature.text.split(" ")[0]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
