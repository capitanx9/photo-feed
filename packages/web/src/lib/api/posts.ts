import axios from 'axios'
import { apiClient } from './client'
import type { components } from './schema'

export type Post = components['schemas']['Post']
export type PostMedia = components['schemas']['PostMedia']
export type PostCreateRequest = components['schemas']['PostCreateRequest']
export type UploadURLRequest = components['schemas']['UploadURLRequestRequest']
export type UploadURLResponse = components['schemas']['UploadURLResponse']

export async function requestUploadURL(payload: UploadURLRequest): Promise<UploadURLResponse> {
  const res = await apiClient.post<UploadURLResponse>('/api/posts/upload-url/', payload)
  return res.data
}

// PUT the raw file bytes straight to S3. The presigned URL embeds the policy;
// we must echo the exact Content-Type that was sent to /upload-url/ or S3
// rejects the upload. withCredentials is OFF for this call — S3 doesn't accept
// our backend's cookies and CORS would block it.
export async function putToS3(
  uploadUrl: string,
  file: File,
  contentType: string,
): Promise<void> {
  await axios.put(uploadUrl, file, {
    headers: { 'Content-Type': contentType },
    withCredentials: false,
  })
}

export async function getMedia(mediaId: number): Promise<PostMedia> {
  const res = await apiClient.get<PostMedia>(`/api/posts/media/${mediaId}/`)
  return res.data
}

export async function createPost(payload: PostCreateRequest): Promise<Post> {
  const res = await apiClient.post<Post>('/api/posts/', payload)
  return res.data
}

export async function getPost(id: number): Promise<Post> {
  const res = await apiClient.get<Post>(`/api/posts/${id}/`)
  return res.data
}
