import { clearToken, getToken } from './auth';
import type { ApiError } from './types';

/** API base URL: explicit env, else same origin; localhost:3000 → backend on 8000 (direct port-forward). */
function getApiBaseUrl(): string {
  const g = typeof globalThis !== 'undefined' ? (globalThis as { process?: { env?: Record<string, string> } }).process?.env : undefined;
  const envUrl = (g?.NEXT_PUBLIC_API_URL ?? '').trim();
  if (envUrl) return envUrl;
  if (typeof window !== 'undefined') {
    // Local dev: regardless of frontend port (3000/3001/etc), backend runs on 8000
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return `http://${window.location.hostname}:8000`;
    }
    return window.location.origin;
  }
  return '/api/proxy';
}

export class AuthError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const baseUrl = getApiBaseUrl();
  const fullUrl = `${baseUrl.replace(/\/$/, '')}${path.startsWith('/') ? path : `/${path}`}`;
  console.log('🔧 Fetching:', fullUrl, baseUrl === 'http://localhost:8000' ? '(Minikube direct)' : '');

  const res = await fetch(fullUrl, {
    ...options,
    headers,
  });

  const isJson = res.headers.get('content-type')?.includes('application/json');
  const body = isJson ? await res.json().catch(() => undefined) : undefined;

  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      clearToken();
      throw new AuthError(body?.detail || 'Unauthorized', res.status);
    }
    
    // Handle validation errors (array of error objects)
    let errorMessage = 'Request failed';
    if (body?.detail) {
      if (Array.isArray(body.detail)) {
        // Format Pydantic validation errors
        errorMessage = body.detail
          .map((err: any) => {
            const field = err.loc?.slice(1).join('.') || 'field';
            return `${field}: ${err.msg || 'Invalid value'}`;
          })
          .join(', ');
      } else if (typeof body.detail === 'string') {
        errorMessage = body.detail;
      } else {
        errorMessage = body.detail?.message || 'Request failed';
      }
    } else if (body?.message) {
      errorMessage = body.message;
    }
    
    const err: ApiError = {
      status: res.status,
      message: errorMessage,
    };
    throw err;
  }

  return body as T;
}
