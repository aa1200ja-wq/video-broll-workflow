import { api } from "./api.js"
import { state, setProject, selectedSources } from "./state.js"
import { bindSceneEvents, renderScenes } from "./scenes.js"
import { bindLibrary, fillLibraryScenes, refreshLibrary } from "./library.js"
import { bindSettings, loadSettings } from "./settings.js"

const $ = selector => document.querySelector(selector)
let toastTimer = null

function notify(message, error = false) {
  const toast = $("#toast")
  toast.textContent = message
  toast.classList.remove("hidden", "error")
  if (error) toast.classList.add("error")
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => toast.classList.add("hidden"), error ? 7000 : 3500)
}

function renderProjects() {
  $("#project-list").innerHTML = state.projects.map(project => `
    <button class="project-item ${state.project?.id === project.id ? "active" : ""}"
      data-project="${project.id}">${project.name}</button>`).join("")
  $("#project-manager-summary").textContent = state.project
    ? `專案管理｜${state.project.name}` : "專案管理"
}

function renderProject() {
  const p = state.project
  $("#project-title").textContent = p?.name || "請建立專案"
  $("#project-meta").textContent = p ? `${p.scenes.length} 個 Scene · ${p.width}×${p.height}` : ""
  if (p) $("#project-format").value = p.width >= p.height ? "16:9" : "9:16"
  $("#script").value = p?.script || ""
  $("#voice").value = p?.voice || "zh-TW-YunJheNeural"
  $("#rate").value = p?.rate || "+0%"
  $("#pitch").value = p?.pitch || "+0Hz"
  renderProjects()
  renderScenes()
  fillLibraryScenes()
}

async function loadProjects(selectFirst = true) {
  state.projects = await api.projects()
  if (selectFirst && !state.project && state.projects.length) {
    await selectProject(state.projects[0].id); return
  }
  renderProject()
}

async function selectProject(id) {
  setProject(await api.project(id))
  renderProject()
  await refreshLibrary("")
}

async function refreshProject(fetch = true) {
  if (!state.project) return
  if (fetch) state.project = await api.project(state.project.id)
  state.projects = state.projects.map(p => p.id === state.project.id ? state.project : p)
  renderProject()
}

function needProject() {
  if (state.project) return true
  notify("請先建立專案", true); return false
}

function bindTabs() {
  document.querySelectorAll(".tab").forEach(button => button.addEventListener("click", async () => {
    document.querySelectorAll(".tab").forEach(x => x.classList.toggle("active", x === button))
    document.querySelectorAll(".tab-panel").forEach(x => x.classList.add("hidden"))
    $(`#${button.dataset.tab}-panel`).classList.remove("hidden")
    if (button.dataset.tab === "library") await refreshLibrary()
  }))
}

function bindProjectActions() {
  $("#create-project").addEventListener("click", async () => {
    const name = $("#new-project-name").value.trim() || "未命名專案"
    try {
      const project = await api.createProject(name)
      state.projects.push(project); setProject(project)
      $("#new-project-name").value = ""; renderProject(); await refreshLibrary("")
      notify("專案已建立")
    } catch (err) { notify(err.message, true) }
  })
  $("#project-list").addEventListener("click", async event => {
    const button = event.target.closest("[data-project]")
    if (!button) return
    try { await selectProject(button.dataset.project) }
    catch (err) { notify(err.message, true) }
  })
}

function bindWorkflow() {
  $("#project-format").addEventListener("change", async () => {
    if (!needProject()) return
    try {
      state.project = await api.setFormat(state.project.id, $("#project-format").value)
      await refreshProject(false)
      state.results = {}
      renderScenes()
      notify("畫面比例已更新，後續搜尋會自動匹配橫式／直式素材")
    } catch (err) { notify(err.message, true) }
  })

  $("#split-script").addEventListener("click", async () => {
    if (!needProject()) return
    try {
      setProject(await api.setScript(state.project.id, $("#script").value))
      renderProject(); await refreshLibrary("")
      notify(`已切成 ${state.project.scenes.length} 個 Scene`)
    } catch (err) { notify(err.message, true) }
  })

  $("#make-tts").addEventListener("click", async () => {
    if (!needProject()) return
    try {
      notify("正在產生旁白與時間碼…")
      state.project = await api.tts(state.project.id, $("#voice").value, $("#rate").value, $("#pitch").value)
      await refreshProject(false); notify("旁白與時間碼完成")
    } catch (err) { notify(err.message, true) }
  })

  $("#search-all").addEventListener("click", async () => {
    if (!needProject()) return
    const queries = $("#bulk-queries").value.split(/\r?\n/).map(x => x.trim()).filter(Boolean)
    if (!queries.length) { notify("請貼入素材搜尋詞", true); return }
    try {
      notify("正在搜尋全部 Scene…")
      state.project = await api.setQueries(state.project.id, queries)
      state.results = await api.searchAll(state.project.id, selectedSources())
      renderProject()
      const count = Object.values(state.results).filter(x => x.length).length
      notify(`搜尋完成：${count}/${state.project.scenes.length} 個 Scene 有候選素材`)
    } catch (err) { notify(err.message, true) }
  })

  $("#make-preview").addEventListener("click", async () => {
    if (!needProject()) return
    try {
      notify("正在產生粗剪預覽…"); await api.preview(state.project.id)
      $("#open-preview").href = api.previewUrl(state.project.id)
      $("#open-preview").classList.remove("disabled"); notify("粗剪預覽完成")
    } catch (err) { notify(err.message, true) }
  })

  $("#export-jianying").addEventListener("click", async () => {
    if (!needProject()) return
    try {
      notify("正在建立剪映草稿…")
      const result = await api.exportJianying(state.project.id, state.project.name)
      notify(`剪映草稿「${result.draft_name}」已建立`)
    } catch (err) { notify(err.message, true) }
  })
}

async function start() {
  bindTabs(); bindProjectActions(); bindWorkflow()
  bindSceneEvents({ notify, refreshProject, refreshLibrary })
  bindLibrary({ notify, refreshProject })
  bindSettings({ notify })
  try {
    await Promise.all([loadSettings(), loadProjects()])
  } catch (err) { notify(err.message, true) }
}

start()
