"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, User, Message, DecryptedMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Send,
  Lock,
  Unlock,
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldQuestion,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  X,
} from "lucide-react";

interface ConversationMessage extends Message {
  decryptedContent?: string;
  isDecrypting?: boolean;
  verificationResult?: {
    is_signature_valid: boolean;
    blockchain_registered: boolean;
  };
}

interface ChatViewProps {
  selectedUser: User;
  currentUserId: number;
}

export function ChatView({ selectedUser, currentUserId }: ChatViewProps) {
  const { password } = useAuth();
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [modalPassword, setModalPassword] = useState("");
  const [decryptingMessageId, setDecryptingMessageId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadMessages = async () => {
    try {
      setIsLoading(true);
      const allMessages = await api.getMessages();
      
      // Filter messages for this conversation
      const conversationMessages = allMessages.filter(
        (msg) =>
          (msg.sender_id === currentUserId && msg.recipient_id === selectedUser.id) ||
          (msg.sender_id === selectedUser.id && msg.recipient_id === currentUserId)
      );
      
      // Sort by ID (chronological)
      conversationMessages.sort((a, b) => a.id - b.id);
      
      setMessages(conversationMessages);
    } catch (err) {
      console.error("Error loading messages:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMessages();
    // Poll for new messages every 5 seconds
    const interval = setInterval(loadMessages, 5000);
    return () => clearInterval(interval);
  }, [selectedUser.id, currentUserId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !password) return;

    setIsSending(true);
    setError("");

    try {
      await api.sendMessage({
        content: newMessage,
        recipient_id: selectedUser.id,
        password: password,
      });
      setNewMessage("");
      await loadMessages();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al enviar mensaje");
    } finally {
      setIsSending(false);
    }
  };

  const handleDecrypt = async (messageId: number, pwd?: string) => {
    const passwordToUse = pwd || password;
    if (!passwordToUse) {
      setDecryptingMessageId(messageId);
      setShowPasswordModal(true);
      return;
    }

    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId ? { ...msg, isDecrypting: true } : msg
      )
    );

    try {
      const result: DecryptedMessage = await api.decryptMessage(messageId, passwordToUse);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, decryptedContent: result.plaintext, isDecrypting: false }
            : msg
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al descifrar");
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, isDecrypting: false } : msg
        )
      );
    }
  };

  const handleVerify = async (messageId: number, pwd?: string) => {
    const passwordToUse = pwd || password;
    if (!passwordToUse) {
      setDecryptingMessageId(messageId);
      setShowPasswordModal(true);
      return;
    }

    try {
      const result = await api.verifyMessage(messageId, passwordToUse);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? {
                ...msg,
                verificationResult: {
                  is_signature_valid: result.is_signature_valid,
                  blockchain_registered: result.blockchain_registered,
                },
                decryptedContent: result.plaintext || msg.decryptedContent,
              }
            : msg
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al verificar");
    }
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (decryptingMessageId && modalPassword) {
      handleDecrypt(decryptingMessageId, modalPassword);
      setShowPasswordModal(false);
      setModalPassword("");
      setDecryptingMessageId(null);
    }
  };

  const getVerificationIcon = (msg: ConversationMessage) => {
    if (msg.verificationResult) {
      if (msg.verificationResult.is_signature_valid) {
        return <ShieldCheck className="h-4 w-4 text-success" />;
      }
      return <ShieldAlert className="h-4 w-4 text-destructive" />;
    }
    
    switch (msg.verification_status) {
      case "VERIFIED":
        return <ShieldCheck className="h-4 w-4 text-success" />;
      case "NOT_VERIFIED":
        return <ShieldAlert className="h-4 w-4 text-destructive" />;
      default:
        return <ShieldQuestion className="h-4 w-4 text-warning" />;
    }
  };

  const isSentByMe = (msg: Message) => msg.sender_id === currentUserId;

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="px-4 py-3 border-b border-border bg-card flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold">
            {selectedUser.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="font-semibold text-foreground">{selectedUser.name}</h2>
            <p className="text-xs text-muted-foreground">{selectedUser.email}</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={loadMessages}
          className="text-muted-foreground hover:text-foreground"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="px-4 py-2 bg-destructive/10 border-b border-destructive/30 flex items-center justify-between">
          <div className="flex items-center gap-2 text-destructive text-sm">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
          <button onClick={() => setError("")} className="text-destructive hover:text-destructive/80">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-pulse text-muted-foreground">Cargando mensajes...</div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Shield className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <p className="text-muted-foreground">No hay mensajes aun</p>
            <p className="text-sm text-muted-foreground/70">
              Inicia la conversacion enviando un mensaje cifrado
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${isSentByMe(msg) ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                  isSentByMe(msg)
                    ? "bg-primary text-primary-foreground rounded-br-md"
                    : "bg-secondary text-secondary-foreground rounded-bl-md"
                }`}
              >
                {/* Message Content */}
                {msg.decryptedContent ? (
                  <div className="space-y-2">
                    <p className="break-words">{msg.decryptedContent}</p>
                    <div className="flex items-center gap-2 text-xs opacity-70">
                      <Unlock className="h-3 w-3" />
                      <span>Descifrado</span>
                      {getVerificationIcon(msg)}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm opacity-70">
                      <Lock className="h-4 w-4" />
                      <span>Mensaje cifrado</span>
                    </div>
                    <p className="text-xs font-mono opacity-50 truncate max-w-[200px]">
                      {msg.ciphertext.substring(0, 30)}...
                    </p>
                    <div className="flex gap-2 mt-2">
                      <Button
                        size="sm"
                        variant={isSentByMe(msg) ? "secondary" : "outline"}
                        onClick={() => handleDecrypt(msg.id)}
                        disabled={msg.isDecrypting}
                        className="text-xs h-7"
                      >
                        {msg.isDecrypting ? (
                          <RefreshCw className="h-3 w-3 animate-spin mr-1" />
                        ) : (
                          <Unlock className="h-3 w-3 mr-1" />
                        )}
                        Descifrar
                      </Button>
                      {!isSentByMe(msg) && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleVerify(msg.id)}
                          className="text-xs h-7"
                        >
                          <Shield className="h-3 w-3 mr-1" />
                          Verificar
                        </Button>
                      )}
                    </div>
                  </div>
                )}

                {/* Verification Result */}
                {msg.verificationResult && (
                  <div
                    className={`mt-2 p-2 rounded-lg text-xs ${
                      msg.verificationResult.is_signature_valid
                        ? "bg-success/20 text-success"
                        : "bg-destructive/20 text-destructive"
                    }`}
                  >
                    <div className="flex items-center gap-1">
                      {msg.verificationResult.is_signature_valid ? (
                        <>
                          <CheckCircle2 className="h-3 w-3" />
                          <span>Firma valida</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="h-3 w-3" />
                          <span>Firma invalida</span>
                        </>
                      )}
                    </div>
                    {msg.verificationResult.blockchain_registered && (
                      <div className="flex items-center gap-1 mt-1">
                        <Shield className="h-3 w-3" />
                        <span>Registrado en blockchain</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Message ID */}
                <div className="text-[10px] mt-1 opacity-40">
                  ID: {msg.id}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="p-4 border-t border-border bg-card">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <Input
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Escribe un mensaje cifrado..."
            className="flex-1 bg-input border-border"
            disabled={isSending}
          />
          <Button type="submit" disabled={isSending || !newMessage.trim()}>
            {isSending ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Firmado con ECDSA + Cifrado AES-256-GCM + Blockchain
        </p>
      </div>

      {/* Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-2xl p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Ingresa tu contrasena</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Necesitas tu contrasena para descifrar este mensaje.
            </p>
            <form onSubmit={handlePasswordSubmit}>
              <Input
                type="password"
                value={modalPassword}
                onChange={(e) => setModalPassword(e.target.value)}
                placeholder="Tu contrasena"
                className="mb-4 bg-input border-border"
              />
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowPasswordModal(false);
                    setModalPassword("");
                    setDecryptingMessageId(null);
                  }}
                  className="flex-1"
                >
                  Cancelar
                </Button>
                <Button type="submit" className="flex-1">
                  Descifrar
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
