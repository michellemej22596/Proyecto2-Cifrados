"use client";

import { useState, useEffect } from "react";
import { api, Alert } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Bell,
  RefreshCw,
  AlertTriangle,
  AlertCircle,
  ShieldAlert,
  CheckCircle2,
} from "lucide-react";

export function AlertsPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [totalAlerts, setTotalAlerts] = useState(0);
  const [criticalCount, setCriticalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const loadAlerts = async () => {
    setIsLoading(true);
    try {
      const data = await api.getAlerts();
      setAlerts(data.alerts);
      setTotalAlerts(data.total_alerts);
      setCriticalCount(data.critical_count);
    } catch (err) {
      console.error("Error loading alerts:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const getAlertIcon = (alert: Alert) => {
    if (alert.is_critical) {
      return <ShieldAlert className="h-5 w-5 text-destructive" />;
    }
    return <AlertTriangle className="h-5 w-5 text-warning" />;
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border bg-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-destructive/10 rounded-xl">
              <Bell className="h-6 w-6 text-destructive" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">Centro de Alertas</h2>
              <p className="text-sm text-muted-foreground">
                {totalAlerts} alertas, {criticalCount} criticas
              </p>
            </div>
          </div>
          <Button variant="outline" onClick={loadAlerts} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
            Actualizar
          </Button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-xl">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="h-4 w-4 text-destructive" />
              <span className="text-sm font-medium text-destructive">Criticas</span>
            </div>
            <p className="text-2xl font-bold text-destructive">{criticalCount}</p>
          </div>
          <div className="p-3 bg-warning/10 border border-warning/30 rounded-xl">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-4 w-4 text-warning" />
              <span className="text-sm font-medium text-warning">Advertencias</span>
            </div>
            <p className="text-2xl font-bold text-warning">{totalAlerts - criticalCount}</p>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-pulse text-muted-foreground">Cargando alertas...</div>
          </div>
        ) : alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="p-4 bg-success/10 rounded-full mb-4">
              <CheckCircle2 className="h-12 w-12 text-success" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">Todo esta seguro</h3>
            <p className="text-muted-foreground">
              No tienes alertas de seguridad pendientes.
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Todos tus mensajes estan verificados correctamente.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl border ${
                  alert.is_critical
                    ? "bg-destructive/10 border-destructive/30"
                    : "bg-warning/10 border-warning/30"
                }`}
              >
                <div className="flex items-start gap-3">
                  {getAlertIcon(alert)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          alert.is_critical
                            ? "bg-destructive/20 text-destructive"
                            : "bg-warning/20 text-warning"
                        }`}
                      >
                        {alert.is_critical ? "CRITICO" : "ADVERTENCIA"}
                      </span>
                      <span className="text-xs text-muted-foreground">{alert.type}</span>
                    </div>
                    <p
                      className={`text-sm font-medium mb-2 ${
                        alert.is_critical ? "text-destructive" : "text-warning"
                      }`}
                    >
                      {alert.description}
                    </p>
                    <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                      <span>Mensaje ID: {alert.message_id}</span>
                      <span>Remitente: {alert.sender_id}</span>
                      <span>Destinatario: {alert.recipient_id}</span>
                    </div>
                    {alert.timestamp && (
                      <p className="text-xs text-muted-foreground mt-2">{alert.timestamp}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
