"use client";

import { AuthProvider } from "@/lib/auth-context";
import { MessagingApp } from "@/components/messaging-app";

export default function ChatPage() {
  return (
    <AuthProvider>
      <MessagingApp />
    </AuthProvider>
  );
}
