"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { User } from "@/lib/api";
import { ContactList } from "@/components/contact-list";
import { ChatView } from "@/components/chat-view";
import { GroupChats } from "@/components/group-chats";
import { BlockchainExplorer } from "@/components/blockchain-explorer";
import { AlertsPanel } from "@/components/alerts-panel";
import { 
  MessageSquare, 
  Shield, 
  Lock, 
  Fingerprint, 
  Link2, 
  ArrowRight,
  Sparkles 
} from "lucide-react";

type ViewType = "chat" | "groups" | "blockchain" | "alerts";

export function MessagingApp() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [activeView, setActiveView] = useState<ViewType>("chat");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="p-4 bg-primary/10 rounded-2xl">
            <Shield className="h-10 w-10 text-primary animate-pulse" />
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
            <span className="text-muted-foreground">Cargando VaultChain...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
          <span className="text-muted-foreground">Redirigiendo...</span>
        </div>
      </div>
    );
  }

  const handleSelectUser = (u: User) => {
    setSelectedUser(u);
    setActiveView("chat");
  };

  const handleNavigate = (view: ViewType) => {
    setActiveView(view);
    if (view !== "chat") {
      setSelectedUser(null);
    }
  };

  const features = [
    {
      icon: Lock,
      title: "Cifrado AES-256-GCM",
      description: "Proteccion militar para tus mensajes",
      color: "from-cyan-500 to-blue-500",
    },
    {
      icon: Fingerprint,
      title: "Firma ECDSA",
      description: "Autenticidad verificable de cada mensaje",
      color: "from-emerald-500 to-teal-500",
    },
    {
      icon: Link2,
      title: "Blockchain Inmutable",
      description: "Registro permanente e inalterable",
      color: "from-violet-500 to-purple-500",
    },
  ];

  return (
    <div className="h-screen flex flex-col lg:flex-row bg-background overflow-hidden">
      {/* Contact List / Sidebar */}
      <ContactList
        selectedUserId={selectedUser?.id || null}
        onSelectUser={handleSelectUser}
        onNavigate={handleNavigate}
        activeView={activeView}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {activeView === "chat" && (
          <>
            {selectedUser ? (
              <ChatView selectedUser={selectedUser} currentUserId={user.id} />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center bg-gradient-to-b from-background to-secondary/10 p-6 lg:p-12">
                {/* Welcome Card */}
                <div className="max-w-lg w-full">
                  <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full text-primary text-sm font-medium mb-6">
                      <Sparkles className="h-4 w-4" />
                      Mensajeria de alta seguridad
                    </div>
                    <div className="p-5 bg-gradient-to-br from-primary/20 to-primary/5 rounded-2xl inline-block mb-6 border border-primary/10">
                      <MessageSquare className="h-14 w-14 text-primary" />
                    </div>
                    <h2 className="text-2xl lg:text-3xl font-bold text-foreground mb-3">
                      Bienvenido, {user.name?.split(" ")[0]}
                    </h2>
                    <p className="text-muted-foreground max-w-md mx-auto">
                      Selecciona un contacto de la lista para iniciar una conversacion 
                      completamente cifrada y verificable.
                    </p>
                  </div>

                  {/* Features Grid */}
                  <div className="grid gap-4">
                    {features.map((feature, i) => (
                      <div 
                        key={i}
                        className="flex items-center gap-4 p-4 bg-card border border-border rounded-xl hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300 cursor-default group"
                      >
                        <div className={`p-3 rounded-xl bg-gradient-to-br ${feature.color} shadow-lg`}>
                          <feature.icon className="h-5 w-5 text-white" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                            {feature.title}
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            {feature.description}
                          </p>
                        </div>
                        <ArrowRight className="h-5 w-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    ))}
                  </div>

                  {/* Security Badge */}
                  <div className="mt-8 flex items-center justify-center gap-3 text-sm text-muted-foreground">
                    <Shield className="h-4 w-4 text-primary" />
                    <span>Tu privacidad es nuestra prioridad</span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {activeView === "groups" && <GroupChats />}
        {activeView === "blockchain" && <BlockchainExplorer />}
        {activeView === "alerts" && <AlertsPanel />}
      </div>
    </div>
  );
}
