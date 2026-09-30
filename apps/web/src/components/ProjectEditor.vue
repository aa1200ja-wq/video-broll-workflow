<script setup lang="ts">
import { ref } from 'vue'
import type { Project } from '../types'
import { api } from '../api'
import SceneCard from './SceneCard.vue'

const props = defineProps<{ project: Project }>()
const emit = defineEmits<{ reload: [] }>()
const busy = ref(false)
const message = ref('')
const draftFolder = ref('')

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
      <textarea class="script" v-model="project.script" placeholder="貼上完整旁白稿" />
      <button @click="saveScript" :disabled="busy">依標點重新切 Scene</button>
    </section>
    <section class="panel tts-row">
      <div><label>聲音</label><input v-model="project.voice" /></div>
      <div><label>語速</label><input v-model="project.rate" /></div>
      <div><label>音調</label><input v-model="project.pitch" /></div>
      <button @click="tts" :disabled="busy">2. 產生旁白＋時間碼</button>
    </section>
    <section class="panel">
      <h3>3. 搜尋／指定每幕素材</h3>
      <SceneCard
        v-for="scene in project.scenes" :key="scene.id"
        :project-id="project.id" :scene="scene"
        @changed="emit('reload')" @split="split" @merge="merge"
      />
    </section>
    <section class="panel export-row">
      <button @click="preview" :disabled="busy">4. 產生粗剪預覽</button>
      <input v-model="draftFolder" placeholder="剪映草稿資料夾，例如 D:\JianyingPro Drafts" />
      <button @click="exportJY" :disabled="busy || !draftFolder">5. 建立剪映草稿</button>
    </section>
    <p v-if="message" class="message">{{ message }}</p>
  </main>
</template>
