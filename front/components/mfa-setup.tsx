"use client";

import { useState, useEffect } from "react";
import { api, MfaSetupData } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Shield,
  ShieldCheck,
  ShieldOff,
  Smartphone,
  Lock,
  Copy,
  Check,
  AlertCircle,
  CheckCircle2,
  X,
  RefreshCw,
  KeyRound,
} from "lucide-react";

interface MfaSetupModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type Step = "status" | "scan" | "confirm" | "disable";

export function MfaSetupModal({ isOpen, onClose }: MfaSetupModalProps) {
  const [step, setStep] = useState<Step>("status");
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [setupData, setSetupData] = useState<MfaSetupData | null>(null);
  const [otpCode, setOtpCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [copied, setCopied] = useState(false);

  // Cargar estado MFA al abrir
  useEffect(() => {
    if (!isOpen) return;
    setStep("status");
    setError("");
    setSuccessMsg("");
    setOtpCode("");
    setSetupData(null);

    api.getMfaStatus().then((s) => setMfaEnabled(s.mfa_enabled));
  }, [isOpen]);

  if (!isOpen) return null;

  // ---- Acciones ----

  const handleStartSetup = async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await api.setupMfa();
      setSetupData(data);
      setStep("scan");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al generar QR");
    } finally {
      setIsLoading(false);
    }
  };

  const handleEnable = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otpCode.length !== 6) return;
    setIsLoading(true);
    setError("");
    try {
      await api.enableMfa(otpCode);
      setMfaEnabled(true);
      setSuccessMsg("¡MFA activado! Tu cuenta ahora requiere un código TOTP al iniciar sesión.");
      setStep("status");
      setOtpCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código incorrecto");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisable = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otpCode.length !== 6) return;
    setIsLoading(true);
    setError("");
    try {
      await api.disableMfa(otpCode);
      setMfaEnabled(false);
      setSuccessMsg("MFA desactivado. El acceso ya no requiere código TOTP.");
      setStep("status");
      setOtpCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código incorrecto");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopySecret = () => {
    if (!setupData) return;
    navigator.clipboard.writeText(setupData.secret).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  // ---- Render ----

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
      <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-md animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-xl">
              <Smartphone className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">Autenticación de dos factores</h2>
              <p className="text-xs text-muted-foreground">
                {mfaEnabled ? "MFA activo en tu cuenta" : "MFA inactivo"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-xl transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Mensajes globales */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/30 rounded-xl text-sm text-destructive animate-in fade-in duration-200">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}
          {successMsg && (
            <div className="flex items-center gap-2 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-sm text-emerald-500 animate-in fade-in duration-200">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              {successMsg}
            </div>
          )}

          {/* ---- PASO: status ---- */}
          {step === "status" && (
            <div className="space-y-4">
              {/* Estado actual */}
              <div className={`flex items-center gap-4 p-4 rounded-xl border ${
                mfaEnabled
                  ? "bg-emerald-500/10 border-emerald-500/30"
                  : "bg-secondary/50 border-border"
              }`}>
                {mfaEnabled
                  ? <ShieldCheck className="h-8 w-8 text-emerald-500 shrink-0" />
                  : <ShieldOff className="h-8 w-8 text-muted-foreground shrink-0" />
                }
                <div>
                  <p className="font-medium text-foreground">
                    {mfaEnabled ? "MFA activado" : "MFA desactivado"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {mfaEnabled
                      ? "Tu cuenta requiere un código TOTP al iniciar sesión."
                      : "Activa MFA para mayor seguridad con tu app autenticadora."}
                  </p>
                </div>
              </div>

              {/* Cómo funciona (solo si inactivo) */}
              {!mfaEnabled && (
                <div className="space-y-2 text-sm text-muted-foreground">
                  <p className="font-medium text-foreground text-xs uppercase tracking-wide">
                    Cómo funciona
                  </p>
                  {[
                    { icon: Smartphone, text: "Instala Google Authenticator, Authy o cualquier app TOTP" },
                    { icon: KeyRound, text: "Escanea el código QR que te mostraremos" },
                    { icon: Shield, text: "Al iniciar sesión usarás tu contraseña + código de 6 dígitos" },
                  ].map(({ icon: Icon, text }, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 bg-secondary/40 rounded-lg">
                      <Icon className="h-4 w-4 text-primary shrink-0" />
                      <span>{text}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Botones de acción */}
              {!mfaEnabled ? (
                <Button
                  onClick={handleStartSetup}
                  disabled={isLoading}
                  className="w-full h-11 shadow-lg shadow-primary/20"
                >
                  {isLoading ? (
                    <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Generando QR...</>
                  ) : (
                    <><ShieldCheck className="h-4 w-4 mr-2" />Activar MFA</>
                  )}
                </Button>
              ) : (
                <Button
                  variant="destructive"
                  onClick={() => { setStep("disable"); setError(""); setSuccessMsg(""); setOtpCode(""); }}
                  className="w-full h-11"
                >
                  <ShieldOff className="h-4 w-4 mr-2" />
                  Desactivar MFA
                </Button>
              )}
            </div>
          )}

          {/* ---- PASO: scan (QR) ---- */}
          {step === "scan" && setupData && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground text-center">
                Escanea este QR con tu app autenticadora. Si no puedes escanearlo,
                ingresa el código secreto manualmente.
              </p>

              {/* QR code */}
              <div className="flex justify-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={setupData.qr_code}
                  alt="QR MFA"
                  className="w-48 h-48 rounded-xl border border-border p-1 bg-white"
                />
              </div>

              {/* Secret manual */}
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Código secreto (entrada manual):</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 font-mono text-xs bg-secondary/50 border border-border rounded-lg px-3 py-2 break-all select-all">
                    {setupData.secret}
                  </code>
                  <button
                    type="button"
                    onClick={handleCopySecret}
                    className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors shrink-0"
                    title="Copiar secreto"
                  >
                    {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <Button
                onClick={() => { setStep("confirm"); setError(""); setOtpCode(""); }}
                className="w-full h-11"
              >
                Ya escaneé el QR →
              </Button>
              <button
                type="button"
                onClick={() => setStep("status")}
                className="w-full text-sm text-muted-foreground hover:text-foreground transition-colors py-1"
              >
                Cancelar
              </button>
            </div>
          )}

          {/* ---- PASO: confirm (verificar que la app funciona) ---- */}
          {step === "confirm" && (
            <form onSubmit={handleEnable} className="space-y-4">
              <div className="text-center space-y-1">
                <Lock className="h-8 w-8 text-primary mx-auto" />
                <p className="font-medium text-foreground">Confirma el código</p>
                <p className="text-sm text-muted-foreground">
                  Ingresa el código de 6 dígitos que muestra tu app para confirmar
                  que la configuración es correcta.
                </p>
              </div>

              <Input
                type="text"
                inputMode="numeric"
                pattern="\d{6}"
                maxLength={6}
                placeholder="000000"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                autoFocus
                className="h-14 text-center text-2xl tracking-[0.5em] font-mono"
              />

              <Button
                type="submit"
                disabled={isLoading || otpCode.length !== 6}
                className="w-full h-11 shadow-lg shadow-primary/20"
              >
                {isLoading ? (
                  <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Verificando...</>
                ) : (
                  <><ShieldCheck className="h-4 w-4 mr-2" />Confirmar y activar MFA</>
                )}
              </Button>
              <button
                type="button"
                onClick={() => setStep("scan")}
                className="w-full text-sm text-muted-foreground hover:text-foreground transition-colors py-1"
              >
                ← Volver al QR
              </button>
            </form>
          )}

          {/* ---- PASO: disable ---- */}
          {step === "disable" && (
            <form onSubmit={handleDisable} className="space-y-4">
              <div className="text-center space-y-1">
                <ShieldOff className="h-8 w-8 text-destructive mx-auto" />
                <p className="font-medium text-foreground">Desactivar MFA</p>
                <p className="text-sm text-muted-foreground">
                  Ingresa el código actual de tu app para confirmar que deseas
                  desactivar la autenticación de dos factores.
                </p>
              </div>

              <Input
                type="text"
                inputMode="numeric"
                pattern="\d{6}"
                maxLength={6}
                placeholder="000000"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                autoFocus
                className="h-14 text-center text-2xl tracking-[0.5em] font-mono"
              />

              <Button
                type="submit"
                variant="destructive"
                disabled={isLoading || otpCode.length !== 6}
                className="w-full h-11"
              >
                {isLoading ? (
                  <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Verificando...</>
                ) : (
                  <><ShieldOff className="h-4 w-4 mr-2" />Confirmar desactivación</>
                )}
              </Button>
              <button
                type="button"
                onClick={() => setStep("status")}
                className="w-full text-sm text-muted-foreground hover:text-foreground transition-colors py-1"
              >
                Cancelar
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
