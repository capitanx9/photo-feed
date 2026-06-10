'use client'

import { useCallback, useRef, useState } from 'react'
import { AxiosError } from 'axios'
import {
  createPost,
  getMedia,
  putToS3,
  requestUploadURL,
  type Post,
} from '@/lib/api/posts'

export type PostCreatePhase =
  | 'idle'
  | 'presigning'
  | 'uploading'
  | 'processing'
  | 'creating'
  | 'done'
  | 'error'

export type PostCreateInput = {
  file: File
  caption: string
  // Decimal-as-string to match the backend serializer (DRF DecimalField).
  price: string | null
}

const POLL_INTERVAL_MS = 1500
// Cut_image Lambda usually finishes in 2-5s; give it generous headroom before
// surfacing a user-visible error so a cold start doesn't look broken.
const POLL_TIMEOUT_MS = 60_000

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function pollMediaReady(
  mediaId: number,
  signal: AbortSignal,
): Promise<void> {
  const deadline = performance.now() + POLL_TIMEOUT_MS
  while (performance.now() < deadline) {
    if (signal.aborted) throw new Error('cancelled')
    const media = await getMedia(mediaId)
    if (media.status === 'ready') return
    if (media.status === 'failed') {
      throw new Error('media processing failed')
    }
    await sleep(POLL_INTERVAL_MS)
  }
  throw new Error('media processing timed out')
}

function extractError(err: unknown): string {
  if (err instanceof AxiosError) {
    const data = err.response?.data as { detail?: string } | undefined
    if (data?.detail) return data.detail
    return err.message
  }
  return err instanceof Error ? err.message : 'unknown error'
}

export function usePostCreate() {
  const [phase, setPhase] = useState<PostCreatePhase>('idle')
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const run = useCallback(async (input: PostCreateInput): Promise<Post | null> => {
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl
    setError(null)

    try {
      setPhase('presigning')
      const presign = await requestUploadURL({
        content_type: input.file.type,
        content_length: input.file.size,
        kind: 'post',
      })

      setPhase('uploading')
      await putToS3(presign.upload_url, input.file, input.file.type)

      setPhase('processing')
      await pollMediaReady(presign.media_id, ctrl.signal)

      setPhase('creating')
      const post = await createPost({
        caption: input.caption,
        price: input.price,
        media_ids: [presign.media_id],
      })

      setPhase('done')
      return post
    } catch (err) {
      if (ctrl.signal.aborted) return null
      setPhase('error')
      setError(extractError(err))
      return null
    }
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setPhase('idle')
    setError(null)
  }, [])

  return { phase, error, run, reset }
}
