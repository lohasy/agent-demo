const API_BASE = "http://localhost:8000"

export async function createSession() {
  const res = await fetch(`${API_BASE}/api/session/new`)
  const data = await res.json()
  return data.session_id
}

export function chatStream(message, sessionId, callbacks) {
  const { onEvent, onDone, onError } = callbacks

  fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  }).then(async (response) => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ""

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n")
      buffer = lines.pop() || ""

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const event = JSON.parse(line.slice(6))
            onEvent(event)
            if (event.type === "done") {
              onDone()
              return
            }
          } catch (e) {
            // skip parse errors
          }
        }
      }
    }
    onDone()
  }).catch(err => {
    onError(err)
  })
}

export async function confirm(sessionId, approved) {
  const res = await fetch(`${API_BASE}/api/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, approved }),
  })
  return res.json()
}
