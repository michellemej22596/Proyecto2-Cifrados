"use client";

import { useState, useEffect } from "react";
import { api, Group, User } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Users,
  Plus,
  Send,
  RefreshCw,
  ArrowLeft,
  Lock,
  X,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

export function GroupChats() {
  const { user, password } = useAuth();
  const [groups, setGroups] = useState<Group[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [selectedMembers, setSelectedMembers] = useState<number[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [newMessage, setNewMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [groupsList, usersList] = await Promise.all([
        api.getGroups(),
        api.getUsers(),
      ]);
      setGroups(groupsList);
      setUsers(usersList.filter((u) => u.id !== user?.id));
    } catch (err) {
      console.error("Error loading data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user?.id]);

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroupName.trim() || selectedMembers.length === 0) return;

    setIsCreating(true);
    setError("");

    try {
      await api.createGroup(newGroupName, selectedMembers);
      setSuccess("Grupo creado exitosamente");
      setShowCreateModal(false);
      setNewGroupName("");
      setSelectedMembers([]);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear grupo");
    } finally {
      setIsCreating(false);
    }
  };

  const handleSendGroupMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedGroup || !password) return;

    setIsSending(true);
    setError("");

    try {
      await api.sendGroupMessage({
        content: newMessage,
        group_id: selectedGroup.id,
        password: password,
      });
      setNewMessage("");
      setSuccess("Mensaje enviado al grupo");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al enviar mensaje");
    } finally {
      setIsSending(false);
    }
  };

  const toggleMember = (userId: number) => {
    setSelectedMembers((prev) =>
      prev.includes(userId)
        ? prev.filter((id) => id !== userId)
        : [...prev, userId]
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border bg-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {selectedGroup && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSelectedGroup(null)}
                className="lg:hidden"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
            )}
            <div className="p-2 bg-primary/10 rounded-xl">
              <Users className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                {selectedGroup ? selectedGroup.name : "Grupos"}
              </h2>
              <p className="text-sm text-muted-foreground">
                {selectedGroup
                  ? `${selectedGroup.members?.length || 0} miembros`
                  : `${groups.length} grupos disponibles`}
              </p>
            </div>
          </div>
          {!selectedGroup && (
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Nuevo Grupo
            </Button>
          )}
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mt-3 p-3 bg-destructive/10 border border-destructive/30 rounded-xl flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error}</span>
            <button onClick={() => setError("")} className="ml-auto">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {success && (
          <div className="mt-3 p-3 bg-success/10 border border-success/30 rounded-xl flex items-center gap-2 text-success">
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-sm">{success}</span>
            <button onClick={() => setSuccess("")} className="ml-auto">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Groups List */}
        <div
          className={`${
            selectedGroup ? "hidden lg:block" : "block"
          } w-full lg:w-80 border-r border-border overflow-y-auto`}
        >
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-pulse text-muted-foreground">Cargando grupos...</div>
            </div>
          ) : groups.length === 0 ? (
            <div className="p-8 text-center">
              <Users className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground mb-4">No hay grupos aun</p>
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Crear Grupo
              </Button>
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {groups.map((group) => (
                <button
                  key={group.id}
                  onClick={() => setSelectedGroup(group)}
                  className={`w-full p-4 rounded-xl text-left transition-colors ${
                    selectedGroup?.id === group.id
                      ? "bg-primary/10 border border-primary/30"
                      : "hover:bg-secondary"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold">
                      {group.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground truncate">{group.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {group.members?.length || 0} miembros
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Group Chat Area */}
        {selectedGroup ? (
          <div className="flex-1 flex flex-col">
            {/* Members */}
            <div className="p-4 border-b border-border bg-secondary/30">
              <p className="text-xs text-muted-foreground mb-2">Miembros del grupo</p>
              <div className="flex flex-wrap gap-2">
                {selectedGroup.members?.map((member) => (
                  <span
                    key={member.id}
                    className="px-2 py-1 bg-secondary rounded-full text-xs text-secondary-foreground"
                  >
                    {member.name}
                  </span>
                ))}
              </div>
            </div>

            {/* Messages Area (placeholder - would need group messages API) */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Lock className="h-12 w-12 text-muted-foreground/30 mb-4" />
                <p className="text-muted-foreground">
                  Envia un mensaje cifrado al grupo
                </p>
                <p className="text-sm text-muted-foreground/70">
                  Todos los miembros podran descifrar el mensaje
                </p>
              </div>
            </div>

            {/* Message Input */}
            <div className="p-4 border-t border-border bg-card">
              <form onSubmit={handleSendGroupMessage} className="flex gap-2">
                <Input
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Mensaje para el grupo..."
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
            </div>
          </div>
        ) : (
          <div className="flex-1 hidden lg:flex items-center justify-center bg-secondary/10">
            <div className="text-center">
              <Users className="h-16 w-16 mx-auto text-muted-foreground/20 mb-4" />
              <p className="text-muted-foreground">Selecciona un grupo para chatear</p>
            </div>
          </div>
        )}
      </div>

      {/* Create Group Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-2xl p-6 max-w-md w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Crear Nuevo Grupo</h3>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewGroupName("");
                  setSelectedMembers([]);
                }}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateGroup}>
              <div className="mb-4">
                <label className="text-sm font-medium text-foreground mb-1.5 block">
                  Nombre del grupo
                </label>
                <Input
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  placeholder="Ej: Equipo de trabajo"
                  className="bg-input border-border"
                />
              </div>

              <div className="mb-4">
                <label className="text-sm font-medium text-foreground mb-1.5 block">
                  Seleccionar miembros ({selectedMembers.length} seleccionados)
                </label>
                <div className="max-h-48 overflow-y-auto border border-border rounded-xl p-2 space-y-1">
                  {users.map((u) => (
                    <button
                      key={u.id}
                      type="button"
                      onClick={() => toggleMember(u.id)}
                      className={`w-full flex items-center gap-3 p-2 rounded-lg transition-colors ${
                        selectedMembers.includes(u.id)
                          ? "bg-primary/20 border border-primary/30"
                          : "hover:bg-secondary"
                      }`}
                    >
                      <div
                        className={`w-5 h-5 rounded-md border-2 flex items-center justify-center ${
                          selectedMembers.includes(u.id)
                            ? "bg-primary border-primary"
                            : "border-border"
                        }`}
                      >
                        {selectedMembers.includes(u.id) && (
                          <CheckCircle2 className="h-3 w-3 text-primary-foreground" />
                        )}
                      </div>
                      <div className="flex-1 text-left">
                        <p className="text-sm font-medium">{u.name}</p>
                        <p className="text-xs text-muted-foreground">{u.email}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewGroupName("");
                    setSelectedMembers([]);
                  }}
                  className="flex-1"
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  disabled={isCreating || !newGroupName.trim() || selectedMembers.length === 0}
                  className="flex-1"
                >
                  {isCreating ? (
                    <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Plus className="h-4 w-4 mr-2" />
                  )}
                  Crear Grupo
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
