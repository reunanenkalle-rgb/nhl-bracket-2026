<template>
    <div class="leaderboard-view">
      <h2>Leaderboard</h2>
      <div v-if="store.isLoadingLeaderboard">Loading leaderboard...</div>
      <table v-else-if="store.leaderboard.length > 0">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Name</th>
            <th>Score</th>
            <th>Correct (%)</th>
            <th>Stanley Cup Pick</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(entry, index) in store.leaderboard" :key="entry.submission_id">
            <td>{{ index + 1 }}</td>
            <td>
              <RouterLink :to="{ name: 'ViewBracket', params: { submissionId: entry.submission_id } }">
                {{ entry.player_name }}
              </RouterLink>
            </td>
            <td>{{ entry.score }}</td>
            <td>{{ entry.percentage_correct }}% ({{ entry.correct_picks }}/{{ entry.completed_series }})</td>
            <td>
              <img v-if="entry.stanley_cup_pick_logo_url" 
                   :src="entry.stanley_cup_pick_logo_url" 
                   :alt="entry.stanley_cup_pick_abbr || 'N/A'" 
                   class="team-logo-small" 
                   :title="entry.stanley_cup_pick_abbr || 'N/A'" />
              <span v-else>N/A</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else>No leaderboard data available yet.</div>
    </div>
  </template>
  
  <script lang="ts" setup>
  import { onMounted } from 'vue';
  import { useBracketStore } from '@/stores/bracketStore'; // Or your dedicated leaderboard store
  import { RouterLink } from 'vue-router';
  
  const store = useBracketStore(); // Or useLeaderboardStore();
  
  onMounted(() => {
    store.fetchLeaderboard();
  });
  </script>
  
  <style scoped>
  .leaderboard-view { /* ... styles ... */ }
  table { width: 100%; border-collapse: collapse; margin-top: 20px; }
  th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
  th { background-color: #f2f2f2; }
  .team-logo-small { width: 24px; height: 24px; vertical-align: middle; }
  /* Add more styles as needed */
  </style>