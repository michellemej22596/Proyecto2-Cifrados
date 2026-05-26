"use client";

import { useState, useEffect } from "react";
import { api, User } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { MfaSetupModal } from "@/components/mfa-setup";
import { Input } from "@/components/ui/input";
import { 
  Search, 
  MessageSquare, 
  Users, 
  Shield, 
  Bell, 
  Link2, 
  LogOut, 
  Menu, 
  X,
  ChevronRight,
  Circle,
  Settings
} from "lucide-react";

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
  const [isHoveringLogout, setIsHoveringLogout] = useState(false);
  const [showMfaModal, setShowMfaModal] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [usersList, alertsData] = await Promise.all([
          api.getUsers(),
          api.getAlerts(),
        ]);
        setUsers(usersList.filter((u) => u.id !== user?.id));
        setAlertCount(alertsData.total_alerts);
      } catch (err) {
        console.error("Error loading data:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
    const interval = setInterval(async () => {
      try {
        const alertsData = await api.getAlerts();
        setAlertCount(alertsData.total_alerts);
      } catch (err) {
        console.error("Error refreshing alerts:", err);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [user?.id]);

  const filteredUsers = users.filter(
    (u) =>
      u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const navItems = [
    { id: "chat" as const, icon: MessageSquare, label: "Chats", description: "Mensajes directos" },
    { id: "groups" as const, icon: Users, label: "Grupos", description: "Conversaciones grupales" },
    { id: "blockchain" as const, icon: Link2, label: "Blockchain", description: "Explorar registros" },
    { id: "alerts" as const, icon: Bell, label: "Alertas", description: "Notificaciones", badge: alertCount },
  ];

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

  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden flex items-center justify-between p-4 border-b border-border bg-card/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-xl">
            <Shield className="h-5 w-5 text-primary" />
          </div>
          <span className="font-bold text-foreground">VaultChain</span>
        </div>
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2.5 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-xl transition-all"
        >
          {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Sidebar */}
      <div
        className={`${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0 fixed lg:static inset-y-0 left-0 z-40 w-80 bg-sidebar border-r border-sidebar-border flex flex-col transition-transform duration-300 ease-out`}
      >
        {/* Header */}
        <div className="p-5 border-b border-sidebar-border">
          <div className="flex items-center gap-3 mb-5">
            <div className="p-2.5 bg-gradient-to-br from-primary/20 to-primary/5 rounded-xl border border-primary/10">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-sidebar-foreground">VaultChain</h1>
              <p className="text-xs text-muted-foreground">Mensajeria Segura</p>
            </div>
          </div>

          {/* User Profile Card */}
          <div className="relative p-4 bg-gradient-to-br from-sidebar-accent to-sidebar-accent/50 rounded-xl border border-sidebar-border/50 overflow-hidden group hover:border-primary/20 transition-all duration-300">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative flex items-center gap-3">
              <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${getAvatarColor(user?.name || "U")} flex items-center justify-center text-white font-semibold text-sm shadow-lg`}>
                {getInitials(user?.name || "Usuario")}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sidebar-foreground truncate">{user?.name}</p>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Circle className="h-2 w-2 fill-emerald-500 text-emerald-500" />
                  <span>En linea</span>
                </div>
              </div>
              <button
                onClick={() => setShowMfaModal(true)}
                title="Configurar autenticación de dos factores"
                className="p-2 text-muted-foreground hover:text-foreground hover:bg-sidebar-accent rounded-lg transition-colors opacity-0 group-hover:opacity-100"
              >
                <Settings className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="p-3 border-b border-sidebar-border">
          <div className="grid grid-cols-4 gap-1.5">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  onNavigate(item.id);
                  setIsMobileMenuOpen(false);
                }}
                className={`relative flex flex-col items-center gap-1.5 p-3 rounded-xl transition-all duration-200 group ${
                  activeView === item.id
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                    : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                }`}
              >
                <item.icon className="h-5 w-5" />
                <span className="text-[10px] font-medium">{item.label}</span>
                {item.badge && item.badge > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 bg-destructive text-destructive-foreground text-[10px] font-bold rounded-full flex items-center justify-center shadow-lg animate-pulse">
                    {item.badge > 99 ? "99+" : item.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Search */}
        {activeView === "chat" && (
          <div className="p-3 border-b border-sidebar-border">
            <div className="relative group">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
              <Input
                placeholder="Buscar contactos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 h-11 bg-sidebar-accent border-sidebar-border focus:ring-2 focus:ring-primary/20 transition-all"
              />
            </div>
          </div>
        )}

        {/* Contact List */}
        {activeView === "chat" && (
          <div className="flex-1 overflow-y-auto p-2">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center h-32 gap-3">
                <div className="w-8 h-8 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
                <span className="text-sm text-muted-foreground">Cargando contactos...</span>
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                <div className="p-4 bg-sidebar-accent rounded-2xl mb-4">
                  <Users className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="font-medium text-foreground mb-1">
                  {searchQuery ? "Sin resultados" : "Sin contactos"}
                </p>
                <p className="text-sm text-muted-foreground">
                  {searchQuery 
                    ? "Intenta con otro termino de busqueda" 
                    : "Los contactos apareceran aqui"}
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredUsers.map((contact, index) => (
                  <button
                    key={contact.id}
                    onClick={() => {
                      onSelectUser(contact);
                      setIsMobileMenuOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all duration-200 group ${
                      selectedUserId === contact.id
                        ? "bg-primary/10 border border-primary/30 shadow-sm"
                        : "hover:bg-sidebar-accent border border-transparent"
                    }`}
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${getAvatarColor(contact.name)} flex items-center justify-center text-white font-semibold text-sm shadow-md shrink-0 group-hover:scale-105 transition-transform`}>
                      {getInitials(contact.name)}
                    </div>
                    <div className="flex-1 min-w-0 text-left">
                      <p className="font-medium text-sidebar-foreground truncate group-hover:text-primary transition-colors">
                        {contact.name}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {contact.email}
                      </p>
                    </div>
                    <ChevronRight className={`h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-all ${
                      selectedUserId === contact.id ? "opacity-100 text-primary" : ""
                    }`} />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Other views info */}
        {activeView !== "chat" && (
          <div className="flex-1 overflow-y-auto p-4 flex items-center justify-center">
            <div className="text-center">
              <div className="p-4 bg-sidebar-accent rounded-2xl inline-block mb-4">
                {activeView === "groups" && <Users className="h-8 w-8 text-muted-foreground" />}
                {activeView === "blockchain" && <Link2 className="h-8 w-8 text-muted-foreground" />}
                {activeView === "alerts" && <Bell className="h-8 w-8 text-muted-foreground" />}
              </div>
              <p className="text-sm text-muted-foreground">
                {activeView === "groups" && "Ver grupos en el panel principal"}
                {activeView === "blockchain" && "Explorar blockchain"}
                {activeView === "alerts" && "Ver alertas de seguridad"}
              </p>
            </div>
          </div>
        )}

        {/* Logout */}
        <div className="p-3 border-t border-sidebar-border">
          <button
            onClick={logout}
            onMouseEnter={() => setIsHoveringLogout(true)}
            onMouseLeave={() => setIsHoveringLogout(false)}
            className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all duration-300 ${
              isHoveringLogout 
                ? "bg-destructive/10 text-destructive" 
                : "text-muted-foreground hover:bg-sidebar-accent"
            }`}
          >
            <LogOut className={`h-5 w-5 transition-transform duration-300 ${isHoveringLogout ? "-translate-x-0.5" : ""}`} />
            <span className="text-sm font-medium">Cerrar sesion</span>
          </button>
        </div>
      </div>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-30 lg:hidden animate-in fade-in duration-200"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* MFA Setup Modal */}
      <MfaSetupModal isOpen={showMfaModal} onClose={() => setShowMfaModal(false)} />
    </>
  );
}
