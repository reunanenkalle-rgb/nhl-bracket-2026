<template>
    <div class="landing-container">
      <div class="glass-card">
        <img src="https://assets.nhle.com/logos/nhl/svg/NHL_light.svg" alt="NHL" class="nhl-logo" />
        <h2>LoLa Viralline 2026</h2>
        <p>Enter the secret access code to join the bracket challenge.</p>
        
        <div class="input-group">
          <input 
            v-model="accessCode" 
            type="password" 
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
  import axios from 'axios';
  
  const accessCode = ref('');
  const error = ref('');
  const isLoading = ref(false);
  const router = useRouter();
  
  const checkCode = async () => {
    if (!accessCode.value) return;
    isLoading.value = true;
    error.value = '';
  
    try {
      // Replace with your actual API URL if different
      const response = await axios.post('http://localhost:5000/api/verify_access', { 
        code: accessCode.value
      });
  
      if (response.data.success) {
        // Store the access flag in localStorage
        localStorage.setItem('lola_access_granted', 'true');
        router.push('/'); // Redirect to the bracket
      }
    } catch (err) {
      error.value = 'Väärä koodi. Try again!';
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