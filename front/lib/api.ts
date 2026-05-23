const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// Helper to extract error message from various error response formats
function extractErrorMessage(error: unknown, fallback: string): string {
  if (!error) return fallback;
  
  // If it's a string, return it
  if (typeof error === 'string') return error;
  
  // If it's an object with detail
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>;
    
    // FastAPI validation errors: {detail: [{msg: "...", loc: [...]}]}
    if (Array.isArray(err.detail)) {
      const messages = err.detail.map((d: unknown) => {
        if (typeof d === 'object' && d !== null) {
          const detail = d as Record<string, unknown>;
          return detail.msg || JSON.stringify(d);
        }
        return String(d);
      });
      return messages.join(', ');
    }
    
    // Simple detail string: {detail: "error message"}
    if (typeof err.detail === 'string') {
      return err.detail;
    }
    
    // Nested detail object: {detail: {message: "..."}}
    if (typeof err.detail === 'object' && err.detail !== null) {
      const detail = err.detail as Record<string, unknown>;
      if (typeof detail.message === 'string') return detail.message;
      if (typeof detail.msg === 'string') return detail.msg;
      return JSON.stringify(err.detail);
    }
    
    // message field
    if (typeof err.message === 'string') {
      return err.message;
    }
    
    // error field
    if (typeof err.error === 'string') {
      return err.error;
    }
  }
  
  return fallback;
}

export interface User {
  id: number;
  name: string;
  email: string;
  public_key_pem?: string;
}

export interface Message {
  id: number;
  sender_id: number;
  recipient_id: number;
  ciphertext: string;
  nonce: string;
  auth_tag?: string;
  encrypted_key?: string;
  signature?: string;
  verification_status: "PENDING" | "VERIFIED" | "NOT_VERIFIED";
  created_at?: string;
}

export interface Group {
  id: number;
  name: string;
  owner_id: number;
}

export interface GroupMessage {
  id: number;
  group_id: number;
  sender_id: number;
  ciphertext: string;
  nonce: string;
  created_at?: string;
}

export interface BlockchainBlock {
  index: number;
  timestamp: string;
  nonce: number;
  sender_id?: string;
  recipient_id?: string;
  message_hash?: string;
  previous_hash: string;
  hash: string;
}

export interface Alert {
  type: string;
  is_critical: boolean;
  message_id: number;
  sender_id: number;
  recipient_id: number;
  description: string;
  timestamp: string;
}

export interface DecryptedMessage {
  plaintext: string;
}

export interface VerificationResult {
  message_id: number;
  sender_id: number;
  recipient_id: number;
  is_signature_valid: boolean;
  signature_status: string;
  blockchain_registered: boolean;
  plaintext?: string;
  message?: string;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async register(data: { name: string; email: string; password: string }) {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(extractErrorMessage(error, `Error ${response.status}`));
    }
    return response.json();
  }

  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(extractErrorMessage(error, "Credenciales invalidas"));
    }
    return response.json();
  }

  async getUsers(): Promise<User[]> {
    const response = await fetch(`${API_BASE}/users/`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) return [];
    return response.json();
  }

  async getMessages(): Promise<Message[]> {
    const response = await fetch(`${API_BASE}/messages/hybrid/`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) return [];
    return response.json();
  }

  async sendMessage(data: { content: string; recipient_id: number; password: string }) {
    const response = await fetch(`${API_BASE}/messages/hybrid/`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(extractErrorMessage(error, `Error ${response.status}`));
    }
    return response.json();
  }

  async decryptMessage(messageId: number, password: string): Promise<DecryptedMessage> {
    const response = await fetch(`${API_BASE}/messages/${messageId}/decrypt`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ password }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(extractErrorMessage(error, `Error ${response.status}`));
    }
    return response.json();
  }

  async verifyMessage(messageId: number, password: string): Promise<VerificationResult> {
    const response = await fetch(`${API_BASE}/messages/${messageId}/verify`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ password }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(extractErrorMessage(error, `Error ${response.status}`));
    }
    return response.json();
  }

  async getAlerts(): Promise<{ total_alerts: number; critical_count: number; alerts: Alert[] }> {
    const response = await fetch(`${API_BASE}/messages/alerts/me`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      return { total_alerts: 0, critical_count: 0, alerts: [] };
    }
    return response.json();
  }

  async getBlockchain(): Promise<{ chain: BlockchainBlock[]; length: number }> {
    const response = await fetch(`${API_BASE}/blockchain/`);
    if (!response.ok) {
      return { chain: [], length: 0 };
    }
    return response.json();
  }

  async verifyBlockchain(): Promise<{ is_valid: boolean; total_blocks: number; message: string }> {
    const response = await fetch(`${API_BASE}/blockchain/verify`);
    if (!response.ok) {
      throw new Error("Error al verificar blockchain");
    }
    return response.json();
  }

  async getGroups(): Promise<Group[]> {
    const response = await fetch(`${API_BASE}/groups/`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) return [];
    return response.json();
  }

  async createGroup(name: string, memberNames: string[]): Promise<Group> {
    const response = await fetch(`${API_BASE}/groups/`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ name, member_names: memberNames }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(extractErrorMessage(error, `Error ${response.status}`));
    }
    return response.json();
  }

  async sendGroupMessage(groupId: number, content: string, password: string): Promise<GroupMessage> {
    const response = await fetch(`${API_BASE}/groups/${groupId}/messages`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ content, password }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(extractErrorMessage(error, `Error ${response.status}`));
    }
    return response.json();
  }

  async getGroupMessages(groupId: number): Promise<GroupMessage[]> {
    const response = await fetch(`${API_BASE}/groups/${groupId}/messages`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) return [];
    return response.json();
  }

  async decryptGroupMessage(groupId: number, messageId: number, password: string): Promise<DecryptedMessage> {
    const response = await fetch(`${API_BASE}/groups/${groupId}/messages/${messageId}/decrypt`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ password }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(extractErrorMessage(error, `Error ${response.status}`));
    }
    return response.json();
  }
}

export const api = new ApiClient();
