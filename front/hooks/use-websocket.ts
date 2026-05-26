"use client";

import { useEffect, useRef } from "react";

/**
 * Convierte la URL base HTTP/HTTPS del API al equivalente WS/WSS.
 * Ej: "http://localhost:8000" → "ws://localhost:8000"
 *     "https://api.example.com" → "wss://api.example.com"
 *
 * NOTA: NEXT_PUBLIC_API_BASE_URL se resuelve en build-time. En desarrollo
 * local sin Docker su valor es el default "http://localhost:8000".
 */
function getWsBaseUrl(): string {
  const apiBase =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  return apiBase
    .replace(/^https:\/\//, "wss://")
    .replace(/^http:\/\//, "ws://");
}

type WsMessageHandler = (data: unknown) => void;

/**
 * Hook que abre y mantiene una conexión WebSocket autenticada con el backend.
 *
 * - Se conecta a ws://<host>/ws/<userId>?token=<jwt>
 * - Si la conexión se cierra inesperadamente, reintenta cada 3 segundos.
 * - El handler `onMessage` se llama cada vez que llega un mensaje JSON del servidor.
 * - Al desmontar el componente la conexión se cierra limpiamente.
 *
 * @param userId   ID del usuario autenticado (null → no conecta)
 * @param token    JWT del usuario (null → no conecta)
 * @param onMessage  Callback que recibe el payload JSON parseado
 */
export function useWebSocket(
  userId: number | null,
  token: string | null,
  onMessage: WsMessageHandler
): void {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Guardamos el handler en un ref para poder actualizarlo sin re-conectar
  const onMessageRef = useRef<WsMessageHandler>(onMessage);
  useEffect(() => {
    onMessageRef.current = onMessage;
  });

  // Indicador de si el hook sigue montado (evita reconectar tras desmontar)
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    if (!userId || !token) return;

    const connect = () => {
      if (!mountedRef.current) return;

      const url = `${getWsBaseUrl()}/ws/${userId}?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        // Limpia cualquier timer de reconexión pendiente
        if (reconnectTimerRef.current) {
          clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        // Ignorar pongs del keep-alive
        if (event.data === "pong") return;
        try {
          const data = JSON.parse(event.data as string);
          onMessageRef.current(data);
        } catch {
          // Ignorar mensajes que no sean JSON válido
        }
      };

      ws.onerror = () => {
        // El onclose se dispara justo después, ahí manejamos la reconexión
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        // Reintenta en 3 s
        reconnectTimerRef.current = setTimeout(connect, 3000);
      };
    };

    connect();

    // Keep-alive: ping al servidor cada 25 s para mantener la conexión
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, 25_000);

    return () => {
      mountedRef.current = false;
      clearInterval(pingInterval);
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        // Evita que el onclose intente reconectar durante el cleanup
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [userId, token]); // Solo reconectar si cambia el usuario o el token
}
