const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function parseOrThrow<T>(path: string, response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const message =
      (body && typeof body === 'object' && 'detail' in body && String(body.detail)) ||
      `Request to ${path} failed with status ${response.status}`
    throw new ApiError(response.status, message)
  }

  return response.json() as Promise<T>
}

/** GET a JSON resource from the backend API. Throws ApiError on any non-2xx response. */
export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`)
  return parseOrThrow<T>(path, response)
}

/** POST a JSON body (or none, for state-transition actions). Throws ApiError on any non-2xx response. */
export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    ...(body !== undefined
      ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
      : {}),
  })
  return parseOrThrow<T>(path, response)
}
