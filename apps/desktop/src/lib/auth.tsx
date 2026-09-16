import type { Device, User } from "@novasoft/shared";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, getStoredDeviceId, getToken, setStoredDeviceId, setToken } from "./api";

interface AuthContextValue {
  user: User | null;
  device: Device | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// Guards against concurrent callers (React StrictMode's double effect invocation, or a fast
// login-then-mount race) racing each other into registering two devices for the same PC.
let inFlightRegistration: Promise<Device> | null = null;

async function ensureDeviceRegistered(): Promise<Device> {
  if (inFlightRegistration) return inFlightRegistration;

  inFlightRegistration = (async () => {
    const existingId = getStoredDeviceId();
    if (existingId) {
      try {
        const devices = await api.get<Device[]>("/devices");
        const found = devices.find((d) => d.id === existingId);
        if (found) return found;
      } catch {
        // fall through and re-register
      }
    }

    const deviceName = `Support device ${crypto.randomUUID().slice(0, 8)}`;

    const devices = await api.get<Device[]>("/devices");
    const existing = devices.find((d) => d.device_name === deviceName);
    const device = existing ?? (await api.post<Device>("/devices", { device_name: deviceName }));
    setStoredDeviceId(device.id);
    return device;
  })();

  try {
    return await inFlightRegistration;
  } finally {
    inFlightRegistration = null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [device, setDevice] = useState<Device | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const me = await api.get<User>("/auth/me");
        setUser(me);
        setDevice(await ensureDeviceRegistered());
      } catch {
        setToken(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function login(email: string, password: string) {
    const { access_token } = await api.post<{ access_token: string }>("/auth/login", { email, password });
    setToken(access_token);
    const me = await api.get<User>("/auth/me");
    setUser(me);
    setDevice(await ensureDeviceRegistered());
  }

  function logout() {
    api.post("/auth/logout").catch(() => undefined);
    setToken(null);
    setUser(null);
    setDevice(null);
  }

  return <AuthContext.Provider value={{ user, device, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
