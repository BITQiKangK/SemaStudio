import { getApiUrl } from '../config/api.js'

/**
 * @param {string} path - API
 * @param {object} options - fetch
 * @returns {Promise<Response>}
 */
export async function apiRequest(path, options = {}) {
  const url = getApiUrl(path)
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  }

  if (options.body instanceof FormData) {
    delete defaultOptions.headers['Content-Type']
  }
  
  return fetch(url, {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers
    }
  })
}

