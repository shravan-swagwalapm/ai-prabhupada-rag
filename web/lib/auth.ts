/**
 * Google Sign-In wrapper + JWT token management.
 *
 * Uses Google Identity Services (GSI) for authentication,
 * stores JWT and user info in localStorage.
 */

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";
const TOKEN_KEY = "prabhupada_token";
const USER_KEY = "prabhupada_user";
const API_BASE = "/api";

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  photo_url: string | null;
  text_quota: number;
  voice_quota: number;
}

interface AuthResult {
  token: string;
  user: UserInfo;
}

/**
 * Initialize Google Sign-In and render the button.
 */
export function initGoogleSignIn(
  buttonElementId: string,
  onSuccess: (user: UserInfo) => void
): void {
  // Load GSI script if not already loaded
  if (typeof window === "undefined") return;

  const existingScript = document.getElementById("google-gsi-script");
  if (existingScript) {
    // Script already loaded, just initialize
    renderGSIButton(buttonElementId, onSuccess);
    return;
  }

  const script = document.createElement("script");
  script.id = "google-gsi-script";
  script.src = "https://accounts.google.com/gsi/client";
  script.async = true;
  script.defer = true;
  script.onload = () => renderGSIButton(buttonElementId, onSuccess);
  document.head.appendChild(script);
}

function renderGSIButton(
  buttonElementId: string,
  onSuccess: (user: UserInfo) => void
): void {
  const google = (window as any).google;
  if (!google?.accounts?.id) return;

  google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: async (response: { credential: string }) => {
      try {
        const result = await loginWithGoogle(response.credential);
        onSuccess(result.user);
      } catch (err) {
        // Auth error — Google button will remain visible for retry
      }
    },
  });

  const buttonEl = document.getElementById(buttonElementId);
  if (buttonEl) {
    google.accounts.id.renderButton(buttonEl, {
      theme: "filled_black",
      size: "large",
      shape: "pill",
      text: "signin_with",
      width: 280,
    });
  }
}

/**
 * Exchange Google ID token for app JWT via backend.
 */
export async function loginWithGoogle(idToken: string): Promise<AuthResult> {
  const res = await fetch(`${API_BASE}/auth/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Authentication failed");
  }

  const data: AuthResult = await res.json();

  // Persist to localStorage
  localStorage.setItem(TOKEN_KEY, data.token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));

  return data;
}

/**
 * Get stored JWT token.
 */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Get stored user info.
 */
export function getUser(): UserInfo | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserInfo;
  } catch {
    return null;
  }
}

/**
 * Update stored user info (e.g., after quota refresh).
 */
export function setUser(user: UserInfo): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Check if user is logged in (token exists and not expired).
 */
export function isLoggedIn(): boolean {
  const token = getToken();
  if (!token) return false;

  try {
    // Decode JWT payload (base64url) to check expiry
    const payload = JSON.parse(atob(token.split(".")[1]));
    const now = Math.floor(Date.now() / 1000);
    return payload.exp > now;
  } catch {
    return false;
  }
}

/**
 * Log out — clear localStorage and redirect to auth page.
 */
export function logout(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  // Replace (not push) so back button doesn't return to authed page
  window.location.replace("/auth/");
}
