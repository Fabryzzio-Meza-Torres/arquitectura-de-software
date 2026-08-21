import { useEffect, useRef } from 'react'

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

