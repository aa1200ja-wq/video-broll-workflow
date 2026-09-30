<script setup lang="ts">
import { ref } from 'vue'
import type { Project, SearchResult } from '../types'
import { api } from '../api'
import SceneCard from './SceneCard.vue'
import MaterialLibrary from './MaterialLibrary.vue'

const props = defineProps<{ project: Project }>()
const emit = defineEmits<{ reload: [] }>()
const busy = ref(false)
const message = ref('')
const draftFolder = ref('')
const bulkQueries = ref('')
const bulkResults = ref<Record<string, SearchResult[]>>({})
const bulkSources = ref(['pexels', 'pixabay', 'wikimedia'])

async function run(task: () => Promise<unknown>, success: string) {
  busy.value = true; message.value = ''
  try { await task(); message.value = success; emit('reload') }
  catch (e) { message.value = `錯誤：${String(e)}` }
  finally { busy.value = false }
}
const saveScript = () => run(() => api.setScript(props.project.id, props.project.script), '已重新切 Scene')
const tts = () => run(() => api.tts(props.project.id, props.project.voice, props.project.rate, props.project.pitch), '旁白與時間碼已完成')
const preview = () => run(() => api.preview(props.project.id), '粗剪預覽已完成')
const exportJY = () => run(() => api.exportJianying(props.project.id, draftFolder.value, props.project.name), '剪映草稿已建立')

async function applyAndSearch() {
  const queries = bulkQueries.value.split(/\r?\n/).map(x => x.trim()).filter(Boolean)
  if (!queries.length) {
    message.value = '請先貼入素材搜尋詞'
    return
  }
  busy.value = true; message.value = '正在搜尋全部 Scene…'
  try {
    props.project.scenes.forEach((scene, index) => {
      scene.search_query = queries[index] || ''
    })
    await api.setSceneQueries(props.project.id, queries)
    bulkResults.value = await api.searchAll(props.project.id, bulkSources.value)
    const count = Object.values(bulkResults.value).filter(items => items.length > 0).length
    message.value = `搜尋完成：${count} / ${props.project.scenes.length} 個 Scene 有候選素材`
  } catch (e) {
    message.value = `錯誤：${String(e)}`
  } finally {
    busy.value = false
  }
}
function split(sceneId: string) {
  const scene = props.project.scenes.find(x => x.id === sceneId)
  if (!scene) return
  const value = window.prompt('從第幾個字切開？', String(Math.floor(scene.narration.length / 2)))
  if (!value) return
  run(() => api.splitScene(props.project.id, sceneId, Number(value)), '已拆分 Scene')
}
const merge = (id: string) => run(() => api.mergeNext(props.project.id, id), '已合併 Scene')
</script>

<template>
  <main class="editor">
    <div class="topbar">
      <div><h2>{{ project.name }}</h2><small>{{ project.scenes.length }} 個 Scene</small></div>
      <a :href="`/api/projects/${project.id}/preview-file`" target="_blank">開啟預覽</a>
    </div>

    <section class="panel">
      <h3>1. 旁白腳本</h3>
      <textarea class="script" v-model="project.script" placeholder="一次貼上完整旁白稿" />
      <button @click="saveScript" :disabled="busy">依標點重新切 Scene</button>
    </section>

    <section class="panel tts-row">
      <div><label>聲音</label><input v-model="project.voice" /></div>
      <div><label>語速</label><input v-model="project.rate" /></div>
      <div><label>音調</label><input v-model="project.pitch" /></div>
      <button @click="tts" :disabled="busy">2. 產生旁白＋時間碼</button>
    </section>

    <section class="panel">
      <h3>3. 素材搜尋詞一次貼上</h3>
      <textarea
        class="script"
        v-model="bulkQueries"
        placeholder="每行一組搜尋詞，會依順序套用到 Scene 1、2、3……"
      />
      <div class="source-row">
        <label v-for="s in ['pexels','pixabay','wikimedia']" :key="s">
          <input type="checkbox" :value="s" v-model="bulkSources" /> {{ s }}
        </label>
        <button @click="applyAndSearch" :disabled="busy">套用並搜尋全部素材</button>
      </div>
    </section>

    <section class="panel">
      <h3>4. 專案素材庫</h3>
      <p class="hint">下載或上傳過的素材只存一份，可用搜尋詞／來源標籤重新找到，再指定給任何 Scene。</p>
      <MaterialLibrary
        :key="project.id"
        :project="project"
        @changed="emit('reload')"
      />
    </section>

    <section class="panel">
      <h3>5. 檢查／替換每幕素材</h3>
      <SceneCard
        v-for="scene in project.scenes" :key="scene.id"
        :project-id="project.id" :scene="scene"
        :preset-candidates="bulkResults[scene.id] || []"
        @changed="emit('reload')" @split="split" @merge="merge"
      />
    </section>

    <section class="panel export-row">
      <button @click="preview" :disabled="busy">6. 產生粗剪預覽</button>
      <input v-model="draftFolder" placeholder="剪映草稿資料夾，例如 D:\JianyingPro Drafts" />
      <button @click="exportJY" :disabled="busy || !draftFolder">7. 建立剪映草稿</button>
    </section>
    <p v-if="message" class="message">{{ message }}</p>
  </main>
</template>
