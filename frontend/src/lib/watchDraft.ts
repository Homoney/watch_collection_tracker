/**
 * Unsaved Add-watch form, kept in this browser so a closed pop-up, a reload
 * or a crash does not lose what was typed. One draft per signed-in user;
 * cleared when the watch is saved or the changes are discarded. Storage can be
 * missing or full (private windows): then there is simply no draft.
 */
import type { WatchCreate } from '@/types'

export interface WatchDraft {
  values: Partial<WatchCreate>
  complications: string[]
}

export const addWatchDraftKey = (userId?: string) => `watch-tracker:add-watch-draft:${userId || 'anon'}`

export function loadDraft(key: string): WatchDraft | null {
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return null
    const draft = JSON.parse(raw) as WatchDraft
    if (!draft || typeof draft.values !== 'object' || !Array.isArray(draft.complications)) return null
    return draft
  } catch {
    return null
  }
}

export function saveDraft(key: string, draft: WatchDraft) {
  try {
    window.localStorage.setItem(key, JSON.stringify(draft))
  } catch {
    // storage full or blocked: keep working without a draft
  }
}

export function clearDraft(key: string) {
  try {
    window.localStorage.removeItem(key)
  } catch {
    // nothing to clear
  }
}
