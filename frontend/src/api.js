// Talks to the FastAPI backend. In dev, Vite proxies /api -> 127.0.0.1:8000
// (see vite.config.js); in production the built app is served by the same
// FastAPI process, so relative paths work unchanged.

export function downloadUrl(artistSlug, filename) {
  return `/api/download/${encodeURIComponent(artistSlug)}/${encodeURIComponent(filename)}`
}

/**
 * POSTs the analysis form and streams back Server-Sent Events, calling
 * `onUpdate` with each parsed JSON state frame as it arrives.
 */
export async function runAnalysis(formData, onUpdate) {
  const res = await fetch('/api/analyze', { method: 'POST', body: formData })

  if (!res.ok) {
    let message = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) message = body.detail
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new Error(message)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let boundary
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)

      const dataLine = rawEvent
        .split('\n')
        .find((line) => line.startsWith('data:'))
      if (!dataLine) continue

      const payload = dataLine.slice(5).trim()
      if (!payload) continue
      onUpdate(JSON.parse(payload))
    }
  }
}
