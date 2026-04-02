
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export { API_BASE_URL }

export function getApiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`

  if (!API_BASE_URL) {
    return normalizedPath
  }

  const baseUrl = API_BASE_URL.replace(/\/$/, '')
  return `${baseUrl}${normalizedPath}`
}

