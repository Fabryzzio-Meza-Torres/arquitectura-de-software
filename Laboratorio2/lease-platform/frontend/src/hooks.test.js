import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readDraft, saveDraft } from './hooks'

describe('24-hour local drafts', () => {
  beforeEach(() => localStorage.clear())

  it('restores a current draft', () => {
    saveDraft('draft', { ruc: '20123456789' })
    expect(readDraft('draft', {})).toEqual({ ruc: '20123456789' })
  })

  it('expires a draft after 24 hours', () => {
    vi.spyOn(Date, 'now').mockReturnValueOnce(0)
    saveDraft('draft', { ruc: '20123456789' })
    vi.spyOn(Date, 'now').mockReturnValueOnce(24 * 60 * 60 * 1000 + 1)
    expect(readDraft('draft', { empty: true })).toEqual({ empty: true })
    vi.restoreAllMocks()
  })
})

