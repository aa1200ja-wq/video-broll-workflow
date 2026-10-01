import { api } from "./api.js"
import { state } from "./state.js"

const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
}[ch]))

export function fillLibraryScenes() {
  const select = document.querySelector("#library-scene")
  const current = select.value
  const scenes = state.project?.scenes || []
  select.innerHTML = '<option value="">選擇要套用的 Scene</option>' +
    scenes.map(s => `<option value="${s.id}">${s.id}</option>`).join("")
  if (scenes.some(s => s.id === current)) select.value = current
}

function assetCard(asset) {
  const url = api.libraryFile(state.project.id, asset.id)
  const preview = asset.media_type === "video"
    ? `<video src="${url}" muted controls preload="metadata"></video>`
    : `<img src="${url}" alt="本機素材" loading="lazy" />`
  const tags = [...asset.search_queries, ...asset.tags]
    .filter((x, i, all) => x && all.indexOf(x) === i).slice(0, 8)
  return `
    <article class="media-card">
      ${preview}
      <div class="media-body">
        <strong title="${esc(asset.title || asset.id)}">${esc(asset.title || asset.id)}</strong>
        <div class="media-meta">${esc(asset.source)}${asset.author ? " · " + esc(asset.author) : ""}</div>
        <div class="tag-row">${tags.map(x => `<span class="tag">${esc(x)}</span>`).join("")}</div>
        ${asset.used_by.length ? `<div class="media-meta">使用中：${asset.used_by.join("、")}</div>` : ""}
        <button data-asset="${esc(asset.id)}" class="primary">套用到選定 Scene</button>
      </div>
    </article>`
}

export async function refreshLibrary(query = null) {
  const grid = document.querySelector("#library-grid")
  if (!state.project) {
    grid.innerHTML = '<p class="hint">請先建立專案。</p>'; return
  }
  const q = query ?? document.querySelector("#library-query").value
  state.library = await api.library(state.project.id, q)
  grid.innerHTML = state.library.length
    ? state.library.map(assetCard).join("")
    : '<p class="hint">目前沒有符合的本機素材。</p>'
  fillLibraryScenes()
}

export function bindLibrary({ notify, refreshProject }) {
  document.querySelector("#library-search").addEventListener("click", async () => {
    try { await refreshLibrary() } catch (err) { notify(err.message, true) }
  })
  document.querySelector("#library-query").addEventListener("keyup", async event => {
    if (event.key !== "Enter") return
    try { await refreshLibrary() } catch (err) { notify(err.message, true) }
  })
  document.querySelector("#library-grid").addEventListener("click", async event => {
    const button = event.target.closest("button[data-asset]")
    if (!button || !state.project) return
    const sceneId = document.querySelector("#library-scene").value
    if (!sceneId) { notify("請先選擇要套用的 Scene", true); return }
    try {
      await api.useLibrary(state.project.id, sceneId, button.dataset.asset)
      await refreshProject()
      await refreshLibrary()
      notify(`素材已套用到 ${sceneId}`)
    } catch (err) { notify(err.message, true) }
  })
}
