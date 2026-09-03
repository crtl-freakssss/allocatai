import type { ApiResponse, ApiErrorEnvelope } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

class ApiClient {
  private getUrl(endpoint: string): string {
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    return `${BASE_URL}${API_PREFIX}${cleanEndpoint}`;
  }

  private async parseResponse<T>(res: Response): Promise<T> {
    const json = await res.json();
    if (!res.ok) {
      const errEnv = json as ApiErrorEnvelope;
      const message = errEnv?.error?.message || `HTTP ${res.status}: ${res.statusText}`;
      const error = new Error(message);
      (error as any).code = errEnv?.error?.code;
      (error as any).details = errEnv?.error?.details;
      throw error;
    }
    const apiRes = json as ApiResponse<T>;
    return apiRes.data;
  }

  async get<T>(endpoint: string): Promise<T> {
    const res = await fetch(this.getUrl(endpoint), {
      headers: {
        Accept: "application/json",
      },
    });
    return this.parseResponse<T>(res);
  }

  async post<T>(endpoint: string, body?: any): Promise<T> {
    const res = await fetch(this.getUrl(endpoint), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.parseResponse<T>(res);
  }

  async upload<T>(endpoint: string, file: File): Promise<T> {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(this.getUrl(endpoint), {
      method: "POST",
      body: formData,
    });
    return this.parseResponse<T>(res);
  }
}

export const apiClient = new ApiClient();
