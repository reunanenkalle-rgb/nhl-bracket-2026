<template>
    <div class="landing-container">
      <div class="glass-card">
        <img src="https://assets.nhle.com/logos/nhl/svg/NHL_light.svg" alt="NHL" class="nhl-logo" />
        <h2>LoLa Viralline 2026</h2>
        <p>Enter the secret access code to join the bracket challenge.</p>
        
        <div class="input-group">
          <input 
            v-model="accessCode" 
            type="text" 
            autocapitalize="none" 
            autocorrect="off"
            spellcheck="false" 
            placeholder="Access Code" 
            @keyup.enter="checkCode"
          />
          <button @click="checkCode" :disabled="isLoading">
            {{ isLoading ? 'Verifying...' : 'Enter' }}
          </button>
        </div>
        
        <p v-if="error" class="error-text">{{ error }}</p>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue';
  import { useRouter } from 'vue-router';
  import apiService from '@/services/apiService'; // Use the service we already fixed!
  
  const accessCode = ref('');
  const error = ref('');
  const isLoading = ref(false);
  const router = useRouter();
  
  const checkCode = async () => {
    if (!accessCode.value) return;
    
    // MOBILE FIX: Remove accidental spaces and force to uppercase
    const sanitizedCode = accessCode.value.trim().toUpperCase();
    
    isLoading.value = true;
    error.value = '';
  
    try {
      // Use the apiService instead of a hardcoded localhost URL
      const response = await apiService.verifyAccess(sanitizedCode);
  
      if (response.data.success) {
        localStorage.setItem('lola_access_granted', 'true');
        router.push('/'); // Redirect to the bracket
      }
    } catch (err: any) {
      // Fix the encoding for "Väärä koodi"
      if (err.response && err.response.status === 401) {
        error.value = 'Väärä koodi. Try again!';
      } else {
        error.value = 'Server error. Is the backend running?';
      }
      console.error('Login error:', err);
    } finally {
      isLoading.value = false;
    }
  };
  </script>
  
  <style scoped>
  .landing-container {
    height: 80vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background: transparent;
  }
  .glass-card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    padding: 40px;
    border-radius: 15px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    text-align: center;
    max-width: 400px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }
  .nhl-logo { width: 60px; margin-bottom: 20px; }
  .input-group { display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }
  input {
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #444;
    background: #222;
    color: white;
    text-align: center;
    font-size: 1.1rem;
  }
  button {
    padding: 12px;
    border-radius: 8px;
    background: #ffc107;
    color: black;
    font-weight: bold;
    border: none;
    cursor: pointer;
  }
  button:disabled { background: #666; }
  .error-text { color: #ff4d4d; margin-top: 15px; font-size: 0.9rem; }
  </style>