<template>
    <div class="playoff-bracket">
      <h1>NHL Playoff Bracket {{ currentYear }}</h1>
      <div class="controls">
        <input type="text" v-model="playerName" placeholder="Enter Your Name" />
      </div>
      <div v-if="bracketStore.isLoading">Loading bracket...</div>
      <div v-if="bracketStore.error" class="error-message">{{ bracketStore.error }}</div>
  
      <div v-if="!bracketStore.isLoading && !bracketStore.error" class="bracket-layout">
        <div v-for="round in rounds" :key="round.roundNumber" class="round-column">
          <h2>{{ round.name }}
            <span v-if="!bracketStore.canAdvanceToRound(round.roundNumber) && round.roundNumber > 1" class="round-locked">(Complete Previous Round)</span>
          </h2>
          <SeriesMatchup
            v-for="series in round.series"
            :key="series.series_identifier"
            :series-data="series"
            :is-disabled="round.roundNumber > 1 && !bracketStore.canAdvanceToRound(round.roundNumber)"
            @pick-made="handlePick"
          />
        </div>
      </div>
       <button 
          @click="submitBracket" 
          :disabled="!bracketStore.isBracketCompletelyPicked || !playerName.trim() || bracketStore.isLoading"
          class="submit-button"
        >
          Submit Bracket
        </button>
        <div v-if="bracketStore.isBracketCompletelyPicked && playerName.trim()">Ready to submit!</div>
    </div>
  </template>
  
  <script lang="ts" setup>
  import { onMounted, computed, ref, watch } from 'vue';
  // Remove direct Series import if it's handled by store
  import { useBracketStore } from '@/stores/bracketStore'; // Import the store
  import SeriesMatchup from './SeriesMatchup.vue';
  
  const bracketStore = useBracketStore();
  const currentYear = new Date().getFullYear();
  
  // Player name local ref, syncs with store
  const playerName = ref(bracketStore.playerName);
  watch(playerName, (newName) => {
    bracketStore.setPlayerName(newName);
  });
  
  
  const roundDefinitions = [
    { roundNumber: 1, name: 'Round 1' },
    { roundNumber: 2, name: 'Conference Semifinals' },
    { roundNumber: 3, name: 'Conference Finals' },
    { roundNumber: 4, name: 'Stanley Cup Final' },
  ];
  
  // Computed property to get series grouped by round from the store
  const rounds = computed(() => {
    return roundDefinitions.map(rd => {
      const seriesForRound = bracketStore.allSeries // Use store's allSeries
        .filter(s => s.round_number === rd.roundNumber)
        .sort((a, b) => {
          const getSortKey = (identifier: string) => {
            if (identifier.startsWith("EC_R")) return `0-${identifier}`;
            if (identifier.startsWith("WC_R")) return `1-${identifier}`;
            return identifier;
          };
          return getSortKey(a.series_identifier).localeCompare(getSortKey(b.series_identifier));
        });
      return {
        ...rd,
        series: seriesForRound,
      };
    });
  });
  
  onMounted(() => {
    bracketStore.fetchBracketStructure();
  });
  
  const handlePick = (seriesId: number, winningTeamId: number | null) => {
    bracketStore.makePick(seriesId, winningTeamId);
  };
  
  const submitBracket = () => {
    bracketStore.submitBracket();
  }
  </script>
  
  <style scoped>
  .playoff-bracket {
    font-family: Arial, sans-serif;
  }
  .controls {
    margin-bottom: 20px;
    text-align: center;
  }
  .controls input {
    padding: 8px;
    font-size: 1em;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  .bracket-layout {
    display: flex;
    flex-direction: row;
    justify-content: space-around;
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 20px;
  }
  .round-column {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 25px;
    padding: 10px;
    min-width: 240px; /* Increased width */
  }
  .round-column h2 {
    margin-bottom: 15px;
    text-align: center;
    font-size: 1.2em;
    color: #333;
  }
  .round-locked {
    font-size: 0.7em;
    color: #999;
    display: block;
  }
  .error-message {
    color: red;
    text-align: center;
    padding: 20px;
  }
  .submit-button {
    display: block;
    margin: 30px auto;
    padding: 12px 25px;
    font-size: 1.1em;
    color: white;
    background-color: #28a745; /* Green */
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }
  .submit-button:hover:not(:disabled) {
    background-color: #218838; /* Darker green */
  }
  .submit-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
  </style>