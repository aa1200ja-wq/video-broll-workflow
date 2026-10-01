import { api } from "./api.js"
import { state, selectedSources } from "./state.js"

const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
}[ch]))

function candidateCard(item, index, sceneId) {
  const meta = [item.source === "local" ? "本機素材" : item.source, item.author]
    .filter(Boolean).join(" · ")
  const preview = item.source === "local" && item.media_type === "video"
    ? `<video src="${esc(item.preview_url)}" muted controls preload="metadata"></video>`
    : `<img src="${esc(item.preview_url)}" alt="候選素材" loading="lazy" />`
  return `
    <article class="media-card">
      ${preview}
      <div class="media-body">
        <div class="media-meta">${esc(meta || item.media_type)}</div>
        <button class="primary" data-action="choose" data-scene="${sceneId}" data-index="${index}">${item.source === "local" ? "使用本機素材" : "使用這個"}</button>
        ${item.page_url ? `<a href="${esc(item.page_url)}" target="_blank" class="media-meta">查看來源</a>` : ""}
      </div>
    </article>`
}

function sceneCard(scene) {
  const candidates = state.results[scene.id] || []
  const time = scene.end > scene.start
    ? `${scene.start.toFixed(1)}–${scene.end.toFixed(1)}s`
    : "尚未產生時間碼"
  return `
    <article class="scene" data-scene="${scene.id}">
      <div class="scene-head">
        <strong>${scene.id}</strong><span>${time}</span>
        ${scene.selected_asset ? '<span class="ok">已選素材</span>' : ""}
      </div>
      <textarea data-field="narration">${esc(scene.narration)}</textarea>
      <div class="scene-search">
        <input data-field="query" value="${esc(scene.search_query)}" placeholder="素材搜尋詞" />
        <button data-action="search">重新搜尋</button>
        <label class="button-link ghost">加入自己的素材
          <input data-action="upload" type="file" accept="video/*,image/*" hidden />
        </label>
      </div>
      <div class="scene-actions">
        <button class="ghost" data-action="split">拆分</button>
        <button class="ghost" data-action="merge">併下一幕</button>
      </div>
      <div class="candidates">
        ${candidates.map((item, i) => candidateCard(item, i, scene.id)).join("")}
      </div>
    </article>`
}

export function renderScenes() {
  const root = document.querySelector("#scene-list")
  const project = state.project
  root.innerHTML = project?.scenes?.length
    ? project.scenes.map(sceneCard).join("")
    : '<p class="hint">貼上腳本並切 Scene 後，這裡會顯示每一幕。</p>'
  document.querySelector("#scene-count").textContent =
    project ? `${project.scenes.length} 個 Scene` : ""
}

function getScene(sceneId) {
  return state.project?.scenes.find(x => x.id === sceneId)
}

async function saveScene(card) {
  const scene = getScene(card.dataset.scene)
  if (!scene) return
  scene.narration = card.querySelector('[data-field="narration"]').value
  scene.search_query = card.querySelector('[data-field="query"]').value
  await api.updateScene(state.project.id, scene)
}

export function bindSceneEvents({ notify, refreshProject, refreshLibrary }) {
  const root = document.querySelector("#scene-list")
  root.addEventListener("change", async event => {
    const card = event.target.closest(".scene")
    if (!card) return
    try {
      if (event.target.dataset.action === "upload") {
        const file = event.target.files?.[0]
        if (!file) return
        notify("正在加入素材…")
        await api.upload(state.project.id, card.dataset.scene, file)
        await refreshProject()
        await refreshLibrary()
        notify("素材已加入並選用")
      } else if (event.target.dataset.field) {
        await saveScene(card)
      }
    } catch (err) { notify(err.message, true) }
  })

  root.addEventListener("click", async event => {
    const button = event.target.closest("button[data-action]")
    if (!button || !state.project) return
    const card = button.closest(".scene")
    const sceneId = card.dataset.scene
    const scene = getScene(sceneId)
    try {
      if (button.dataset.action === "search") {
        await saveScene(card)
        notify(`${sceneId} 搜尋中…`)
        state.results[sceneId] = await api.search(
          card.querySelector('[data-field="query"]').value, selectedSources())
        renderScenes()
        notify(`${sceneId} 找到 ${state.results[sceneId].length} 個候選素材`)
      }
      if (button.dataset.action === "choose") {
        const item = state.results[sceneId]?.[Number(button.dataset.index)]
        if (!item) return
        notify("正在下載並加入素材庫…")
        await api.choose(state.project.id, sceneId, item)
        await refreshProject()
        await refreshLibrary()
        notify(`${sceneId} 已選用素材`)
      }
      if (button.dataset.action === "split" && scene) {
        const pos = Number(prompt("從第幾個字切開？", Math.floor(scene.narration.length / 2)))
        if (!pos) return
        state.project = await api.splitScene(state.project.id, sceneId, pos)
        state.results = {}
        refreshProject(false)
        notify("Scene 已拆分，請重新產生旁白時間碼")
      }
      if (button.dataset.action === "merge") {
        state.project = await api.mergeScene(state.project.id, sceneId)
        state.results = {}
        refreshProject(false)
        notify("Scene 已合併，請重新產生旁白時間碼")
      }
    } catch (err) { notify(err.message, true) }
  })
}
