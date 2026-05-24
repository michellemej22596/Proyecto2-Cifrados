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
  MoreVertical,
  Phone,
  Video,
  Info,
  Smile,
  Paperclip,
  Mic,
  Check,
  CheckCheck,
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
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadMessages = async () => {
    try {
      setIsLoading(true);
      const allMessages = await api.getMessages();
      
      const conversationMessages = allMessages.filter(
        (msg) =>
          (msg.sender_id === currentUserId && msg.recipient_id === selectedUser.id) ||
          (msg.sender_id === selectedUser.id && msg.recipient_id === currentUserId)
      );
      
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
    const interval = setInterval(loadMessages, 5000);
    return () => clearInterval(interval);
  }, [selectedUser.id, currentUserId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [selectedUser.id]);

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
      inputRef.current?.focus();
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
        return <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />;
      }
      return <ShieldAlert className="h-3.5 w-3.5 text-destructive" />;
    }
    
    switch (msg.verification_status) {
      case "VERIFIED":
        return <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />;
      case "NOT_VERIFIED":
        return <ShieldAlert className="h-3.5 w-3.5 text-destructive" />;
      default:
        return <ShieldQuestion className="h-3.5 w-3.5 text-amber-500" />;
    }
  };

  const isSentByMe = (msg: Message) => msg.sender_id === currentUserId;

  const getInitials = (name: string) => {
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };

  const getAvatarColor = (name: string) => {
    const colors = [
      "from-cyan-500 to-blue-500",
      "from-emerald-500 to-teal-500",
      "from-violet-500 to-purple-500",
      "from-rose-500 to-pink-500",
      "from-amber-500 to-orange-500",
    ];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  const formatTime = (index: number) => {
    const now = new Date();
    const offset = (messages.length - index - 1) * 2;
    const time = new Date(now.getTime() - offset * 60000);
    return time.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-background to-secondary/5">
      {/* Chat Header */}
      <div className="px-4 lg:px-6 py-4 border-b border-border bg-card/80 backdrop-blur-sm flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${getAvatarColor(selectedUser.name)} flex items-center justify-center text-white font-semibold shadow-lg`}>
            {getInitials(selectedUser.name)}
          </div>
          <div>
            <h2 className="font-semibold text-foreground">{selectedUser.name}</h2>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                En linea
              </span>
              <span className="text-border">|</span>
              <span className="flex items-center gap-1">
                <Shield className="h-3 w-3 text-primary" />
                Cifrado E2E
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground rounded-xl h-10 w-10">
            <Phone className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground rounded-xl h-10 w-10">
            <Video className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={loadMessages}
            className="text-muted-foreground hover:text-foreground rounded-xl h-10 w-10"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground rounded-xl h-10 w-10">
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="px-4 py-3 bg-destructive/10 border-b border-destructive/30 flex items-center justify-between animate-in slide-in-from-top duration-300">
          <div className="flex items-center gap-2 text-destructive text-sm">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
          <button 
            onClick={() => setError("")} 
            className="text-destructive hover:text-destructive/80 p-1 hover:bg-destructive/10 rounded transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-4">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <div className="w-10 h-10 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
            <span className="text-sm text-muted-foreground">Cargando mensajes...</span>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="p-6 bg-card border border-border rounded-2xl shadow-lg mb-6">
              <div className="p-4 bg-primary/10 rounded-full inline-block mb-4">
                <Shield className="h-10 w-10 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Chat Cifrado
              </h3>
              <p className="text-muted-foreground text-sm max-w-xs mb-4">
                Inicia una conversacion segura con {selectedUser.name}. 
                Todos los mensajes estan protegidos con cifrado de extremo a extremo.
              </p>
              <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground bg-secondary/50 px-3 py-2 rounded-lg">
                <Lock className="h-3.5 w-3.5 text-primary" />
                <span>AES-256-GCM + ECDSA</span>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => (
              <div
                key={msg.id}
                className={`flex ${isSentByMe(msg) ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2 duration-300`}
                style={{ animationDelay: `${index * 30}ms` }}
              >
                <div className={`max-w-[80%] lg:max-w-[65%] ${isSentByMe(msg) ? "" : "flex gap-3"}`}>
                  {/* Avatar for received messages */}
                  {!isSentByMe(msg) && (
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${getAvatarColor(selectedUser.name)} flex items-center justify-center text-white text-xs font-semibold shrink-0 mt-1`}>
                      {getInitials(selectedUser.name)}
                    </div>
                  )}
                  
                  <div
                    className={`rounded-2xl px-4 py-3 shadow-sm ${
                      isSentByMe(msg)
                        ? "bg-primary text-primary-foreground rounded-br-md"
                        : "bg-card border border-border text-card-foreground rounded-bl-md"
                    }`}
                  >
                    {/* Message Content */}
                    {msg.decryptedContent ? (
                      <div className="space-y-2">
                        <p className="break-words leading-relaxed">{msg.decryptedContent}</p>
                        <div className={`flex items-center justify-between gap-3 text-xs ${isSentByMe(msg) ? "opacity-70" : "text-muted-foreground"}`}>
                          <div className="flex items-center gap-1.5">
                            <Unlock className="h-3 w-3" />
                            <span>Descifrado</span>
                            {getVerificationIcon(msg)}
                          </div>
                          <div className="flex items-center gap-1">
                            <span>{formatTime(index)}</span>
                            {isSentByMe(msg) && <CheckCheck className="h-3.5 w-3.5" />}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className={`flex items-center gap-2 text-sm ${isSentByMe(msg) ? "opacity-80" : "text-muted-foreground"}`}>
                          <Lock className="h-4 w-4" />
                          <span>Mensaje cifrado</span>
                        </div>
                        <div className={`font-mono text-xs ${isSentByMe(msg) ? "opacity-50" : "text-muted-foreground/70"} truncate max-w-[220px] bg-black/10 px-2 py-1 rounded`}>
                          {msg.ciphertext.substring(0, 32)}...
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant={isSentByMe(msg) ? "secondary" : "outline"}
                            onClick={() => handleDecrypt(msg.id)}
                            disabled={msg.isDecrypting}
                            className="text-xs h-8 rounded-lg"
                          >
                            {msg.isDecrypting ? (
                              <>
                                <RefreshCw className="h-3 w-3 animate-spin mr-1.5" />
                                Descifrando...
                              </>
                            ) : (
                              <>
                                <Unlock className="h-3 w-3 mr-1.5" />
                                Descifrar
                              </>
                            )}
                          </Button>
                          {!isSentByMe(msg) && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleVerify(msg.id)}
                              className="text-xs h-8 rounded-lg"
                            >
                              <Shield className="h-3 w-3 mr-1.5" />
                              Verificar
                            </Button>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Verification Result */}
                    {msg.verificationResult && (
                      <div
                        className={`mt-3 p-2.5 rounded-lg text-xs ${
                          msg.verificationResult.is_signature_valid
                            ? "bg-emerald-500/20 text-emerald-200"
                            : "bg-destructive/20 text-destructive"
                        }`}
                      >
                        <div className="flex items-center gap-1.5">
                          {msg.verificationResult.is_signature_valid ? (
                            <>
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              <span className="font-medium">Firma ECDSA valida</span>
                            </>
                          ) : (
                            <>
                              <AlertCircle className="h-3.5 w-3.5" />
                              <span className="font-medium">Firma invalida</span>
                            </>
                          )}
                        </div>
                        {msg.verificationResult.blockchain_registered && (
                          <div className="flex items-center gap-1.5 mt-1.5 opacity-80">
                            <Shield className="h-3 w-3" />
                            <span>Registrado en blockchain</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Typing indicator */}
            {isTyping && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
                <span>{selectedUser.name} esta escribiendo...</span>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="p-4 lg:p-6 border-t border-border bg-card/80 backdrop-blur-sm">
        <form onSubmit={handleSendMessage} className="flex items-end gap-3">
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Escribe un mensaje cifrado..."
              className="h-12 pr-24 bg-input border-border rounded-xl focus:ring-2 focus:ring-primary/20 transition-all"
              disabled={isSending}
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
              <button type="button" className="p-2 text-muted-foreground hover:text-foreground transition-colors rounded-lg hover:bg-secondary">
                <Smile className="h-5 w-5" />
              </button>
              <button type="button" className="p-2 text-muted-foreground hover:text-foreground transition-colors rounded-lg hover:bg-secondary">
                <Paperclip className="h-5 w-5" />
              </button>
            </div>
          </div>
          <Button 
            type="submit" 
            disabled={isSending || !newMessage.trim()}
            className="h-12 w-12 rounded-xl shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all"
          >
            {isSending ? (
              <RefreshCw className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </form>
        <div className="flex items-center justify-center gap-2 mt-3 text-xs text-muted-foreground">
          <Lock className="h-3 w-3 text-primary" />
          <span>Cifrado de extremo a extremo activado</span>
        </div>
      </div>

      {/* Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
          <div className="bg-card border border-border rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="text-center mb-6">
              <div className="p-3 bg-primary/10 rounded-full inline-block mb-3">
                <Lock className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold">Ingresa tu contrasena</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Necesitas tu contrasena para descifrar este mensaje.
              </p>
            </div>
            <form onSubmit={handlePasswordSubmit}>
              <Input
                type="password"
                value={modalPassword}
                onChange={(e) => setModalPassword(e.target.value)}
                placeholder="Tu contrasena"
                className="mb-4 h-12 bg-input border-border"
                autoFocus
              />
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowPasswordModal(false);
                    setModalPassword("");
                    setDecryptingMessageId(null);
                  }}
                  className="flex-1 h-11"
                >
                  Cancelar
                </Button>
                <Button type="submit" className="flex-1 h-11">
                  <Unlock className="h-4 w-4 mr-2" />
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
