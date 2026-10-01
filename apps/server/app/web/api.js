async function request(url, options = {}) {
  const res = await fetch(url, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail || res.statusText)
  }
  const type = res.headers.get("content-type") || ""
  return type.includes("application/json") ? res.json() : res.text()
}

const json = (body, method = "POST") => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
})

export const api = {
  projects: () => request("/api/projects"),
  createProject: name => request("/api/projects", json({ name })),
  project: id => request(`/api/projects/${id}`),
  setScript: (id, script) => request(`/api/projects/${id}/script`, json({ script }, "PUT")),
  updateScene: (id, scene) => request(
    `/api/projects/${id}/scenes/${scene.id}`,
    json({ narration: scene.narration, search_query: scene.search_query }, "PUT")),
  splitScene: (id, sceneId, position) => request(
    `/api/projects/${id}/scenes/${sceneId}/split`, json({ position })),
  mergeScene: (id, sceneId) => request(
    `/api/projects/${id}/scenes/${sceneId}/merge-next`, json({})),
  tts: (id, voice, rate, pitch) => request(
    `/api/projects/${id}/tts`, json({ voice, rate, pitch })),
  setQueries: (id, queries) => request(
    `/api/projects/${id}/scene-queries`, json({ queries }, "PUT")),
  searchAll: (id, sources) => request(
    `/api/projects/${id}/search-all`, json({ sources })),
  search: (q, sources) => request(
    `/api/search?q=${encodeURIComponent(q)}&sources=${sources.join(",")}`),
  choose: (id, sceneId, result) => request(
    `/api/projects/${id}/scenes/${sceneId}/download`, json({ result })),
  upload: async (id, sceneId, file) => {
    const form = new FormData(); form.append("file", file)
    return request(`/api/projects/${id}/scenes/${sceneId}/upload`, { method: "POST", body: form })
  },
  preview: id => request(`/api/projects/${id}/preview`, json({ burn_subtitles: false })),
  previewUrl: id => `/api/projects/${id}/preview-file?t=${Date.now()}`,
  exportJianying: (id, name) => request(
    `/api/projects/${id}/export/jianying`, json({ draft_folder: "", draft_name: name })),
  library: (id, q = "") => request(
    `/api/projects/${id}/library?q=${encodeURIComponent(q)}`),
  libraryFile: (id, assetId) =>
    `/api/projects/${id}/library/${encodeURIComponent(assetId)}/file`,
  useLibrary: (id, sceneId, assetId) => request(
    `/api/projects/${id}/scenes/${sceneId}/use-library/${encodeURIComponent(assetId)}`, json({})),
  settings: () => request("/api/settings"),
  saveSettings: body => request("/api/settings", json(body, "PUT")),
  detectJianying: () => request("/api/system/jianying-dirs"),
}
