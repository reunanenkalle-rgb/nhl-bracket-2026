<template>
    <div class="playoff-bracket-page">
      <h1>NHL Playoff Bracket {{ currentYear }}</h1>
      
      <div v-if="bracketStore.isLoading && !bracketStore.successMessage && !bracketStore.error" class="message loading-message">
        Loading bracket data...
      </div>
      <div v-if="bracketStore.successMessage" class="message success-message">
        {{ bracketStore.successMessage }}
      </div>
      <div v-if="bracketStore.error" class="message error-message">
        {{ bracketStore.error }}
      </div>
  
      <div class="controls">
        <input 
          type="text" 
          v-model="localPlayerName" 
          placeholder="Enter Your Name" 
          @input="handleNameInput" 
          :disabled="bracketStore.isLoading"
        />
      </div>
  
      <div v-if="!bracketStore.isLoading && bracketStore.allSeries.length > 0" class="bracket-container">
        <div class="conference-bracket west-conference">
          <div v-for="round in westernConferenceRounds" :key="'wc-r'+round.roundNumber" 
               class="round-column"
               :class="`round-${round.roundNumber}`">
            <h3 class="round-title">{{ round.name }}</h3>
            <SeriesMatchup
              v-for="series in round.series"
              :key="series.series_identifier"
              :series-data="series"
              :is-disabled="isSeriesVisuallyDisabled(series, round.roundNumber)"
              @pick-made="handlePick"
            />
          </div>
        </div>
  
        <div class="final-column round-column round-4">
           <h3 class="round-title">{{ stanleyCupFinalRoundInfo.name }}</h3>
          <SeriesMatchup
            v-if="stanleyCupFinalSeries"
            :key="stanleyCupFinalSeries.series_identifier"
            :series-data="stanleyCupFinalSeries"
            :is-disabled="isSeriesVisuallyDisabled(stanleyCupFinalSeries, stanleyCupFinalRoundInfo.roundNumber)"
            @pick-made="handlePick"
          />
        </div>
  
        <div class="conference-bracket east-conference">
          <div v-for="round in easternConferenceRounds" :key="'ec-r'+round.roundNumber" 
               class="round-column"
               :class="`round-${round.roundNumber}`">
            <h3 class="round-title">{{ round.name }}</h3>
            <SeriesMatchup
              v-for="series in round.series"
              :key="series.series_identifier"
              :series-data="series"
              :is-disabled="isSeriesVisuallyDisabled(series, round.roundNumber)"
              @pick-made="handlePick"
            />
          </div>
        </div>
      </div>
      <div v-else-if="!bracketStore.isLoading && !bracketStore.error">
          <p class="message info-message">No bracket data to display. The bracket might not be set up yet.</p>
      </div>
  
      <button 
        @click="attemptSubmitBracket" 
        :disabled="!canSubmit"
        class="submit-button"
      >
        <span v-if="submitting">Submitting...</span>
        <span v-else>Submit Bracket</span>
      </button>
  
      <div v-if="!bracketStore.isLoading && !bracketStore.successMessage" class="submit-status">
          <span v-if="canSubmit">Ready to submit!</span>
          <span v-else-if="!localPlayerName.trim()">Please enter your name.</span>
          <span v-else-if="!bracketStore.isBracketCompletelyPicked">Please complete all 15 picks.</span>
      </div>
    </div>
  </template>
  
  <script lang="ts" setup>
  import { ref, onMounted, computed, watch } from 'vue';
  import { useBracketStore } from '@/stores/bracketStore';
  import SeriesMatchup from './SeriesMatchup.vue';
  import type { Series } from '@/types';
  
  const bracketStore = useBracketStore();
  const currentYear = new Date().getFullYear();
  const localPlayerName = ref(bracketStore.playerName);
  const submitting = ref(false);
  
  watch(localPlayerName, (newName) => {
    bracketStore.setPlayerName(newName);
  });
  watch(() => bracketStore.playerName, (newName) => {
      if (localPlayerName.value !== newName) localPlayerName.value = newName;
  });
  
  const roundNames: Record<number, string> = {
    1: 'Round 1',
    2: 'Conference Semifinals',
    3: 'Conference Finals',
    4: 'Stanley Cup Final',
  };
  
  const sortSeriesByIdentifier = (seriesArray: Series[]): Series[] => {
    return [...seriesArray].sort((a, b) => {
      // Basic sort, ensures M1, M2, M3, M4 order within a round/conf
      return a.series_identifier.localeCompare(b.series_identifier);
    });
  };
  
  const createConferenceRounds = (conferencePrefix: 'WC' | 'EC') => {
    const roundsOutput = [];
    for (let i = 1; i <= 3; i++) { // Rounds 1, 2, 3 for conference
      const seriesForRound = sortSeriesByIdentifier(
        bracketStore.allSeries.filter(s => s.round_number === i && s.series_identifier.startsWith(conferencePrefix))
      );
      if (seriesForRound.length > 0 || i === 1 || i === 2 || i === 3) { // Ensure round column exists even if empty initially for layout
        roundsOutput.push({
          roundNumber: i,
          name: roundNames[i],
          series: seriesForRound,
        });
      }
    }
    return roundsOutput;
  };
  
  const westernConferenceRounds = computed(() => createConferenceRounds('WC'));
  const easternConferenceRounds = computed(() => createConferenceRounds('EC'));
  
  const stanleyCupFinalSeries = computed(() => 
    bracketStore.allSeries.find(s => s.round_number === 4 && s.series_identifier === 'SCF')
  );
  
  const stanleyCupFinalRoundInfo = computed(() => ({
    roundNumber: 4,
    name: roundNames[4],
  }));
  
  // Determines if a series matchup should be visually disabled for picking
  const isSeriesVisuallyDisabled = (series: Series | undefined, roundNumber: number): boolean => {
    if (!series) return true;
    const teamsNotSet = !series.team1_id || !series.team2_id;
    const previousRoundLock = roundNumber > 1 && !bracketStore.canAdvanceToRound(roundNumber);
    return series.status !== 'PENDING' || teamsNotSet || previousRoundLock;
  };
  
  
  onMounted(async () => {
  if (bracketStore.allSeries.length === 0) {
    await bracketStore.fetchBracketStructure(); // Await this
  }
  // Fetch official results after structure is loaded, or on a timer/button
  // For simplicity, fetch once after initial load.
  if (bracketStore.allSeries.length > 0) { // Ensure structure is there
      await bracketStore.fetchOfficialResults();
  }
});
  
  const handlePick = (seriesId: number, winningTeamId: number | null) => {
    bracketStore.successMessage = null;
    bracketStore.error = null;
    bracketStore.makePick(seriesId, winningTeamId);
  };
  
  const handleNameInput = () => {
      bracketStore.successMessage = null;
      bracketStore.error = null;
  };
  
  const canSubmit = computed(() => 
    bracketStore.isBracketCompletelyPicked && 
    localPlayerName.value.trim() !== '' && 
    !bracketStore.isLoading
  );
  
  const attemptSubmitBracket = async () => {
    bracketStore.successMessage = null;
    bracketStore.error = null;
    submitting.value = true;
    await bracketStore.submitBracket();
    submitting.value = false;
  };
  </script>
  
  <style scoped>
  .playoff-bracket-page { /* Renamed main container class */
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    padding: 10px;
  }
  
  .controls { /* Styles from previous App.vue */
    margin-bottom: 25px;
    text-align: center;
  }
  .controls input[type="text"] {
    padding: 10px 15px;
    font-size: 1.1em;
    border: 1px solid #ccc;
    border-radius: 4px;
    min-width: 300px;
    box-sizing: border-box;
  }
  .controls input[type="text"]:focus {
    border-color: #007bff;
    outline: none;
    box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
  }
  
  .bracket-container {
    display: flex;
    justify-content: space-between; /* Pushes West to left, East to right, Final in middle */
    align-items: flex-start; /* Align conference blocks at their top */
    overflow-x: auto; /* Allow horizontal scrolling on smaller screens */
    padding: 20px 0;
    gap:10px; /* Gap between major sections (West, Final, East) */
  }
  
  .conference-bracket {
    display: flex;
    gap: 10px; /* Gap between round columns within a conference */
  }
  
  .west-conference {
    /* No specific flex order, default is left-to-right */
  }
  
  .east-conference {
    flex-direction: row-reverse; /* Rounds will appear R3, R2, R1 from left to right */
  }
  .east-conference .round-column {
    /* If needed, specific styling for East columns if they need to mirror content order */
  }
  
  
  .round-column {
    display: flex;
    flex-direction: column;
    align-items: center;  /* Let SeriesMatchup define its width */
    gap: 5px; /* Increased vertical gap between matchups for traditional bracket look */
    padding: 0 5px; /* Minimal horizontal padding */
    min-width: auto; /* Ensure matchups have enough space */
  }
  
  /* Specific alignment for matchups in different rounds to create the tree effect */
  /* This part is tricky and needs careful adjustment based on SeriesMatchup height */
  /* .round-column.round-1 .series-matchup { margin-bottom: 10px; } */
  .round-column.round-2 { justify-content: center; padding-top: 0px; /* Example: push R2 down */ }
  .round-column.round-3 { justify-content: center; padding-top: 0px; /* Example: push R3 further down */ }
  .final-column.round-4 { justify-content: center; align-items: center; padding-top: 197px; /* Final in middle */ }
  
  
  .round-title { /* Renamed from .round-column h2 for clarity */
    margin-bottom: 10px;
    text-align: center;
    font-size: 1.1em;
    color: #333;
    font-weight: 600;
    /* white-space: nowrap; */
    max-width: 150px;
    line-height: 1.3;
    word-wrap: break-word;
  }
  
  .round-locked {
    font-size: 0.65em;
    color: #e74c3c;
    display: block;
    font-weight: normal;
    margin-top: 4px;
  }
  
  .final-column {
    display: flex;
    flex-direction: column;
    align-items: center; /* Center the final matchup */
    justify-content: center; /* Vertically center if it has extra space */
    min-width: 180px; /* Slightly wider for emphasis */
    padding-top: 200px; /* Align with conference finals roughly */
  }
  
  
  /* Message styles (success, error, info, loading) - copied from previous */
  .message {
    padding: 12px 15px;
    margin: 15px auto;
    max-width: 80%;
    border-radius: 5px;
    text-align: center;
    font-size: 0.95em;
    border: 1px solid transparent;
  }
  .loading-message { background-color: #e9ecef; color: #495057; border-color: #ced4da; }
  .success-message { background-color: #d1e7dd; color: #0f5132; border-color: #badbcc; }
  .error-message { background-color: #f8d7da; color: #842029; border-color: #f5c2c7; }
  .info-message { background-color: #cce5ff; color: #004085; border-color: #b8daff; }
  
  /* Submit button and status styles - copied from previous */
  .submit-button {
    display: block;
    margin: 40px auto 20px auto;
    padding: 12px 30px;
    font-size: 1.2em;
    font-weight: bold;
    color: white;
    background-color: #007bff;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.2s ease, opacity 0.2s ease;
  }
  .submit-button:hover:not(:disabled) { background-color: #0056b3; }
  .submit-button:disabled { background-color: #ced4da; cursor: not-allowed; opacity: 0.7; }
  .submit-status {
    text-align: center;
    margin-top: 10px;
    font-size: 0.9em;
    color: #555;
    height: 1.2em;
  }
  </style>S