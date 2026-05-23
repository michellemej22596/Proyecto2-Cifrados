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
import { MessageSquare, Shield } from "lucide-react";

type ViewType = "chat" | "groups" | "blockchain" | "alerts";

export function MessagingApp() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [activeView, setActiveView] = useState<ViewType>("chat");

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-primary">Verificando sesion...</div>
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
              <div className="flex-1 flex flex-col items-center justify-center bg-secondary/10 p-8">
                <div className="p-6 bg-card border border-border rounded-2xl text-center max-w-md">
                  <div className="p-4 bg-primary/10 rounded-full inline-block mb-4">
                    <MessageSquare className="h-12 w-12 text-primary" />
                  </div>
                  <h2 className="text-xl font-semibold text-foreground mb-2">
                    Bienvenido a VaultChain
                  </h2>
                  <p className="text-muted-foreground mb-4">
                    Selecciona un contacto de la lista para iniciar una conversacion cifrada.
                  </p>
                  <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                    <Shield className="h-4 w-4 text-primary" />
                    <span>Cifrado de extremo a extremo con AES-256-GCM</span>
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
