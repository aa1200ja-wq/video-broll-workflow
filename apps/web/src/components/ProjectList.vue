<script setup lang="ts">
import { ref } from 'vue'
import type { Project } from '../types'

defineProps<{ projects: Project[]; activeId: string | null }>()
const emit = defineEmits<{ select: [id: string]; create: [name: string] }>()
const name = ref('')
const create = () => {
  if (!name.value.trim()) return
  emit('create', name.value.trim())
  name.value = ''
}
</script>

<template>
  <aside class="sidebar">
    <h1>B-roll Workflow</h1>
    <div class="create-row">
      <input v-model="name" placeholder="新專案名稱" @keyup.enter="create" />
      <button @click="create">新增</button>
    </div>
    <button
      v-for="project in projects" :key="project.id"
      class="project-btn" :class="{ active: project.id === activeId }"
      @click="emit('select', project.id)"
    >{{ project.name }}</button>
  </aside>
</template>
