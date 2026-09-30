<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import type { MaterialAsset, Project } from '../types'
import { api } from '../api'

const props = defineProps<{ project: Project }>()
const emit = defineEmits<{ changed: [] }>()
const items = ref<MaterialAsset[]>([])
const query = ref('')
const sceneId = ref(props.project.scenes[0]?.id || '')
const busy = ref(false)
const error = ref('')

async function load() {
  busy.value = true; error.value = ''
  try { items.value = await api.library(props.project.id, query.value) }
  catch (e) { error.value = String(e) }
  finally { busy.value = false }
}
async function assign(asset: MaterialAsset) {
  if (!sceneId.value) return
  busy.value = true; error.value = ''
  try {
    await api.useLibrary(props.project.id, sceneId.value, asset.id)
    await load()
    emit('changed')
  } catch (e) { error.value = String(e); busy.value = false }
}
watch(() => props.project.id, () => {
  sceneId.value = props.project.scenes[0]?.id || ''
  load()
})
onMounted(load)
</script>

<template>
  <section class="material-library">
    <div class="library-toolbar">
      <input v-model="query" placeholder="搜尋已下載素材：海浪、ocean、coast…" @keyup.enter="load" />
      <button @click="load" :disabled="busy">搜尋素材庫</button>
      <select v-model="sceneId">
        <option value="">選擇要套用的 Scene</option>
        <option v-for="scene in project.scenes" :key="scene.id" :value="scene.id">
          {{ scene.id }}
        </option>
      </select>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="!items.length" class="library-empty">目前沒有符合的本機素材。</p>
    <div v-else class="library-grid">
      <article v-for="asset in items" :key="asset.id" class="library-item">
        <video
          v-if="asset.media_type === 'video'"
          :src="api.libraryFile(project.id, asset.id)"
          muted controls preload="metadata"
        />
        <img v-else :src="api.libraryFile(project.id, asset.id)" alt="本機素材" />
        <strong>{{ asset.title || asset.id }}</strong>
        <small>{{ asset.source }}<span v-if="asset.author"> · {{ asset.author }}</span></small>
        <div class="tag-row">
          <span v-for="tag in [...asset.search_queries, ...asset.tags].slice(0, 8)" :key="tag">{{ tag }}</span>
        </div>
        <small v-if="asset.used_by.length">使用中：{{ asset.used_by.join('、') }}</small>
        <button @click="assign(asset)" :disabled="busy || !sceneId">套用到 {{ sceneId || 'Scene' }}</button>
      </article>
    </div>
  </section>
</template>
