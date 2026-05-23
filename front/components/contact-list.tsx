"use client";

import { useState, useEffect } from "react";
import { api, User } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { Input } from "@/components/ui/input";
import { Search, MessageSquare, Users, Shield, Bell, Link2, LogOut, Menu, X } from "lucide-react";

interface ContactListProps {
  selectedUserId: number | null;
  onSelectUser: (user: User) => void;
  onNavigate: (view: "chat" | "groups" | "blockchain" | "alerts") => void;
  activeView: "chat" | "groups" | "blockchain" | "alerts";
}

export function ContactList({ selectedUserId, onSelectUser, onNavigate, activeView }: ContactListProps) {
  const { user, logout } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [alertCount, setAlertCount] = useState(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [usersList, alertsData] = await Promise.all([
          api.getUsers(),
          api.getAlerts(),
        ]);
        // Filter out current user
        setUsers(usersList.filter((u) => u.id !== user?.id));
        setAlertCount(alertsData.total_alerts);
      } catch (err) {
        console.error("Error loading data:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
    // Refresh alerts every 30 seconds
    const interval = setInterval(async () => {
      const alertsData = await api.getAlerts();
      setAlertCount(alertsData.total_alerts);
    }, 30000);

    return () => clearInterval(interval);
  }, [user?.id]);

  const filteredUsers = users.filter(
    (u) =>
      u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const navItems = [
    { id: "chat" as const, icon: MessageSquare, label: "Mensajes" },
    { id: "groups" as const, icon: Users, label: "Grupos" },
    { id: "blockchain" as const, icon: Link2, label: "Blockchain" },
    { id: "alerts" as const, icon: Bell, label: "Alertas", badge: alertCount },
  ];

  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden flex items-center justify-between p-4 border-b border-border bg-card">
        <div className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-primary" />
          <span className="font-bold text-foreground">VaultChain</span>
        </div>
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 text-muted-foreground hover:text-foreground"
        >
          {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Sidebar */}
      <div
        className={`${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0 fixed lg:static inset-y-0 left-0 z-40 w-80 bg-sidebar border-r border-sidebar-border flex flex-col transition-transform duration-200`}
      >
        {/* Header */}
        <div className="p-4 border-b border-sidebar-border">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-sidebar-primary/10 rounded-xl">
              <Shield className="h-6 w-6 text-sidebar-primary" />
            </div>
            <div>
              <h1 className="font-bold text-sidebar-foreground">VaultChain</h1>
              <p className="text-xs text-muted-foreground">Mensajeria Segura</p>
            </div>
          </div>

          {/* User Info */}
          <div className="flex items-center gap-3 p-3 bg-sidebar-accent rounded-xl">
            <div className="w-10 h-10 rounded-full bg-sidebar-primary/20 flex items-center justify-center text-sidebar-primary font-semibold">
              {user?.name?.charAt(0).toUpperCase() || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sidebar-foreground truncate">{user?.name}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="p-2 border-b border-sidebar-border">
          <div className="flex gap-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  onNavigate(item.id);
                  setIsMobileMenuOpen(false);
                }}
                className={`flex-1 flex flex-col items-center gap-1 p-2 rounded-lg transition-colors relative ${
                  activeView === item.id
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                }`}
              >
                <item.icon className="h-5 w-5" />
                <span className="text-[10px]">{item.label}</span>
                {item.badge && item.badge > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 bg-destructive text-destructive-foreground text-[10px] rounded-full flex items-center justify-center">
                    {item.badge > 9 ? "9+" : item.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Search */}
        {activeView === "chat" && (
          <div className="p-3 border-b border-sidebar-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar contactos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-sidebar-accent border-sidebar-border"
              />
            </div>
          </div>
        )}

        {/* Contact List */}
        {activeView === "chat" && (
          <div className="flex-1 overflow-y-auto p-2">
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-pulse text-muted-foreground">Cargando...</div>
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                {searchQuery ? "No se encontraron contactos" : "No hay contactos disponibles"}
              </div>
            ) : (
              <div className="space-y-1">
                {filteredUsers.map((contact) => (
                  <button
                    key={contact.id}
                    onClick={() => {
                      onSelectUser(contact);
                      setIsMobileMenuOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${
                      selectedUserId === contact.id
                        ? "bg-sidebar-primary/10 border border-sidebar-primary/30"
                        : "hover:bg-sidebar-accent"
                    }`}
                  >
                    <div className="w-10 h-10 rounded-full bg-sidebar-primary/20 flex items-center justify-center text-sidebar-primary font-semibold shrink-0">
                      {contact.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0 text-left">
                      <p className="font-medium text-sidebar-foreground truncate">
                        {contact.name}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        ID: {contact.id}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Other views placeholder content in sidebar */}
        {activeView !== "chat" && (
          <div className="flex-1 overflow-y-auto p-4">
            <p className="text-muted-foreground text-sm text-center">
              {activeView === "groups" && "Grupos disponibles en el panel principal"}
              {activeView === "blockchain" && "Blockchain disponible en el panel principal"}
              {activeView === "alerts" && "Alertas disponibles en el panel principal"}
            </p>
          </div>
        )}

        {/* Logout */}
        <div className="p-3 border-t border-sidebar-border">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 p-3 rounded-xl text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
          >
            <LogOut className="h-5 w-5" />
            <span className="text-sm font-medium">Cerrar sesion</span>
          </button>
        </div>
      </div>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </>
  );
}
