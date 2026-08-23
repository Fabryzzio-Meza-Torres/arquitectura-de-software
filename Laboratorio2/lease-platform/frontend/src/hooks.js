import { useEffect, useRef } from 'react'

// Guards an async load() against out-of-order responses: usePolling, an explicit
// post-action refresh, and a selection-change effect can all fire concurrently, and
// without this a slower *older* response can overwrite a faster *newer* one, producing
// a visible flicker as state alternates between two snapshots. Only the latest call's
// result is ever applied.
export function useRequestSequence() {
  const ref = useRef(0)
  return {
    start: () => (ref.current += 1),
    isCurrent: (seq) => seq === ref.current,
  }
}

export function usePolling(callback, interval = 5000) {
  const callbackRef = useRef(callback)
  callbackRef.current = callback
  useEffect(() => {
    callbackRef.current()
    const id = setInterval(() => callbackRef.current(), interval)
    return () => clearInterval(id)
  }, [interval])
}

export function readDraft(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    const parsed = JSON.parse(raw)
    if (Date.now() - parsed.savedAt > 24 * 60 * 60 * 1000) {
      localStorage.removeItem(key)
      return fallback
    }
    return parsed.value
  } catch {
    return fallback
  }
}

export function saveDraft(key, value) {
  localStorage.setItem(key, JSON.stringify({ savedAt: Date.now(), value }))
}

