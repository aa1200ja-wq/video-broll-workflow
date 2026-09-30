<script setup lang="ts">
import { ref } from 'vue'
import type { Scene, SearchResult } from '../types'
import { api } from '../api'

const props = defineProps<{ projectId: string; scene: Scene }>()
const emit = defineEmits<{ changed: []; split: [sceneId: string]; merge: [sceneId: string] }>()
const candidates = ref<SearchResult[]>([])
const busy = ref(false)
const error = ref('')
const sources = ref(['pexels', 'pixabay', 'wikimedia'])

async function save() {
  await api.updateScene(props.projectId, props.scene)
  emit('changed')
}
async function search() {
  if (!props.scene.search_query.trim()) return
  busy.value = true; error.value = ''
  try { candidates.value = await api.search(props.scene.search_query, sources.value) }
  catch (e) { error.value = String(e) }
  finally { busy.value = false }
}
async function choose(item: SearchResult) {
  busy.value = true; error.value = ''
  try { await api.download(props.projectId, props.scene.id, item); emit('changed') }
  catch (e) { error.value = String(e) }
  finally { busy.value = false }
}
async function upload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]; if (!file) return
  busy.value = true
  try { await api.upload(props.projectId, props.scene.id, file); emit('changed') }
  finally { busy.value = false; input.value = '' }
}
</script>

<template>
  <section class="scene-card">
    <header>
      <strong>{{ scene.id }}</strong>
      <span>{{ scene.start.toFixed(1) }}–{{ scene.end.toFixed(1) }}s</span>
      <span v-if="scene.selected_asset" class="ok">已選素材</span>
    </header>
    <textarea v-model="scene.narration" @change="save" />
    <div class="search-row">
      <input v-model="scene.search_query" placeholder="輸入素材搜尋字，例如 remote island aerial" @change="save" @keyup.enter="search" />
      <button @click="search" :disabled="busy">搜尋</button>
      <label class="upload-btn">加入自己的素材<input type="file" accept="video/*,image/*" @change="upload" /></label>
    </div>
    <div class="source-row">
      <label v-for="s in ['pexels','pixabay','wikimedia']" :key="s">
        <input type="checkbox" :value="s" v-model="sources" /> {{ s }}
      </label>
      <button class="ghost" @click="emit('split', scene.id)">拆分</button>
      <button class="ghost" @click="emit('merge', scene.id)">併下一幕</button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <div v-if="candidates.length" class="candidates">
      <button v-for="item in candidates" :key="item.id" class="candidate" @click="choose(item)">
        <video v-if="item.media_type === 'video'" :src="item.preview_url" muted playsinline />
        <img v-else :src="item.preview_url" alt="候選素材" />
        <span>{{ item.source }} · 使用</span>
      </button>
    </div>
  </section>
</template>
