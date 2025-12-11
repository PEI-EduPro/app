

class ApiClient {
  private baseUrl: string;
  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`);
    if (!response.ok) {
      throw new Error(`Error fetching ${endpoint}: ${response.statusText}`);
    }
    return response.json();
  }
  
  async post<T>(endpoint: string, data: unknown, options?: { headers?: Record<string, string> }): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options?.headers,
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers,
      body: typeof data === 'string' && headers['Content-Type'] === 'application/xml' 
        ? data 
        : JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Error posting to ${endpoint}: ${response.statusText}`);
    }
    return response.json();
  }

  async put<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Error updating ${endpoint}: ${response.statusText}`);
    }
    return response.json();
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Error deleting ${endpoint}: ${response.statusText}`);
    }
    return response.json();
  }
}

export const apiClient = new ApiClient(import.meta.env.VITE_API_URL);