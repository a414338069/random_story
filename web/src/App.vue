<script setup lang="ts">
import { NConfigProvider, zhCN } from 'naive-ui'
import { themeOverrides } from './styles/theme'

import './styles/variables.css'
import './styles/animations.css'
import './styles/mobile.css'
</script>

<template>
  <NConfigProvider :locale="zhCN" :theme-overrides="themeOverrides">
    <div id="app-root">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
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
  font-family: 'Noto Serif SC', 'STSong', 'SimSun', serif;
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
