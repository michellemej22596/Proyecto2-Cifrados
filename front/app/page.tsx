"use client";

import { AuthProvider } from "@/lib/auth-context";
import { AuthForm } from "@/components/auth-form";

export default function HomePage() {
  return (
    <AuthProvider>
      <AuthForm />
    </AuthProvider>
  );
}
