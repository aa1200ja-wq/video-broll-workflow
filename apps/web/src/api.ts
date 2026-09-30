import type { MaterialAsset, Project, SearchResult, Scene } from './types'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail || res.statusText)
  }
  return res.json()
}

const json = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  projects: () => request<Project[]>('/api/projects'),
  create: (name: string) => request<Project>('/api/projects', json({ name })),
  get: (id: string) => request<Project>(`/api/projects/${id}`),
  library: (id: string, q = '') => request<MaterialAsset[]>(
    `/api/projects/${id}/library?q=${encodeURIComponent(q)}`),
  libraryFile: (id: string, assetId: string) =>
    `/api/projects/${id}/library/${encodeURIComponent(assetId)}/file`,
  useLibrary: (id: string, sceneId: string, assetId: string) => request<Project>(
    `/api/projects/${id}/scenes/${sceneId}/use-library/${encodeURIComponent(assetId)}`,
    json({})),
  setScript: (id: string, script: string) => request<Project>(
    `/api/projects/${id}/script`, { ...json({ script }), method: 'PUT' }),
  setSceneQueries: (id: string, queries: string[]) => request<Project>(
    `/api/projects/${id}/scene-queries`,
    { ...json({ queries }), method: 'PUT' }),
  searchAll: (id: string, sources: string[]) => request<Record<string, SearchResult[]>>(
    `/api/projects/${id}/search-all`, json({ sources })),
  updateScene: (id: string, scene: Scene) => request<Project>(
    `/api/projects/${id}/scenes/${scene.id}`,
    { ...json({ narration: scene.narration, search_query: scene.search_query }), method: 'PUT' }),
  splitScene: (id: string, sceneId: string, position: number) => request<Project>(
    `/api/projects/${id}/scenes/${sceneId}/split`, json({ position })),
  mergeNext: (id: string, sceneId: string) => request<Project>(
    `/api/projects/${id}/scenes/${sceneId}/merge-next`, json({})),
  tts: (id: string, voice: string, rate: string, pitch: string) => request<Project>(
    `/api/projects/${id}/tts`, json({ voice, rate, pitch })),
  search: (q: string, sources: string[]) => request<SearchResult[]>(
    `/api/search?q=${encodeURIComponent(q)}&sources=${sources.join(',')}`),
  download: (id: string, sceneId: string, result: SearchResult) => request<Project>(
    `/api/projects/${id}/scenes/${sceneId}/download`, json({ result })),
  upload: async (id: string, sceneId: string, file: File) => {
    const form = new FormData(); form.append('file', file)
    return request<Project>(`/api/projects/${id}/scenes/${sceneId}/upload`, { method: 'POST', body: form })
  },
  preview: (id: string, burn = false) => request<{ path: string }>(
    `/api/projects/${id}/preview`, json({ burn_subtitles: burn })),
  exportJianying: (id: string, draft_folder: string, draft_name?: string) => request(
    `/api/projects/${id}/export/jianying`, json({ draft_folder, draft_name })),
}
