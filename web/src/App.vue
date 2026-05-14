<script setup lang="ts">
import { NConfigProvider, NMessageProvider, NDialogProvider, zhCN } from 'naive-ui'
import { themeOverrides } from './styles/theme'

import './styles/variables.css'
import './styles/animations.css'
import './styles/mobile.css'
</script>

<template>
  <NConfigProvider :locale="zhCN" :theme-overrides="themeOverrides">
    <NMessageProvider>
      <NDialogProvider>
        <div id="app-root" class="rice-paper">
          <router-view v-slot="{ Component, route }">
            <component :is="Component" :key="route.path" />
          </router-view>
        </div>
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>

<style>
* {
  box-sizing: border-box;
}

html, body, #app-root {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  max-width: 100vw;
  overflow-x: hidden;
  font-family: var(--font-family);
  -webkit-font-smoothing: antialiased;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
