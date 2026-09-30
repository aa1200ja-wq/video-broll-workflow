<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from './api'
import type { Project } from './types'
import ProjectList from './components/ProjectList.vue'
import ProjectEditor from './components/ProjectEditor.vue'

const projects = ref<Project[]>([])
const active = ref<Project | null>(null)
const error = ref('')

async function refreshList() {
  projects.value = await api.projects()
}
async function select(id: string) {
  active.value = await api.get(id)
}
async function reload() {
  if (active.value) await select(active.value.id)
  await refreshList()
}
async function create(name: string) {
  try { active.value = await api.create(name); await refreshList() }
  catch (e) { error.value = String(e) }
}
onMounted(async () => {
  try { await refreshList(); if (projects.value[0]) await select(projects.value[0].id) }
  catch (e) { error.value = String(e) }
})
</script>

<template>
  <div class="layout">
    <ProjectList :projects="projects" :active-id="active?.id ?? null" @select="select" @create="create" />
    <ProjectEditor v-if="active" :project="active" @reload="reload" />
    <main v-else class="empty"><h2>建立第一個影片專案</h2><p>左側輸入名稱後即可開始。</p></main>
    <div v-if="error" class="global-error">{{ error }}</div>
  </div>
</template>
