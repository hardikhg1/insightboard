/**
 * main.js — Application entry point.
 *
 * This is the very first file Vite loads. It:
 *  1. Creates the Vue app
 *  2. Registers the router (so <RouterView> and <RouterLink> work everywhere)
 *  3. Mounts the app onto the <div id="app"> in index.html
 */
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)

app.use(router)   // install Vue Router
app.mount('#app') // attach the app to the DOM
