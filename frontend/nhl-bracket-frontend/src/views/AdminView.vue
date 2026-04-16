<template>
    <div class="admin-page">
      <div class="admin-card">
        <h1>Commissioner's Office 2026</h1>
        <div class="action-section">
          <h3>Live Data Sync</h3>
          <p>Sync your local database with the official NHL API results.</p>
          <button @click="runSync" :disabled="loading" class="btn-sync">
            {{ loading ? 'Synchronizing...' : 'Sync NHL Results Now' }}
          </button>
        </div>
  
        <div v-if="logs" class="log-window">
          <h4>Sync Output:</h4>
          <pre>{{ logs }}</pre>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue';
  import axios from 'axios';
  
  const loading = ref(false);
  const logs = ref('');
  
  const runSync = async () => {
    loading.value = true;
    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || 'https://nhl-bracket-2026-production.up.railway.app/api';
      const res = await axios.post(`${apiBase}/admin/update-official-results`);
      logs.value = res.data.output || res.data.error;
    } catch (err) {
      logs.value = "Failed to connect to backend.";
    } finally {
      loading.value = false;
    }
  };
  </script>
  
  <style scoped>
  .admin-page { padding: 40px; display: flex; justify-content: center; background: #121212; min-height: 100vh; color: white; }
  .admin-card { background: #1e1e1e; padding: 30px; border-radius: 12px; width: 100%; max-width: 800px; border: 1px solid #333; }
  .btn-sync { background: #ffc107; color: black; border: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; cursor: pointer; }
  .log-window { margin-top: 20px; background: #000; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 0.85rem; color: #00ff00; overflow-x: auto; }
  </style>