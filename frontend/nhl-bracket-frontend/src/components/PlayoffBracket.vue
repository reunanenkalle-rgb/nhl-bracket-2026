<template>
  <div class="playoff-bracket-page">
    <header class="bracket-header">
      <div class="header-content">
        <h1>NHL Playoff Bracket {{ currentYear }}</h1>
        <div class="controls">
          <input 
            type="text" 
            v-model="localPlayerName" 
            placeholder="Enter Your Name" 
            @input="handleNameInput"
          />
        </div>
      </div>
    </header>

    <div class="message-area">
      <div v-if="bracketStore.isLoading" class="message loading">Loading...</div>
      <div v-if="bracketStore.successMessage" class="message success">{{ bracketStore.successMessage }}</div>
      <div v-if="bracketStore.error" class="message error">{{ bracketStore.error }}</div>
    </div>

    <main v-if="!bracketStore.isLoading" class="bracket-wrapper">
      <div class="bracket-display">
        
        <div v-for="round in westernConferenceRounds" :key="'w'+round.roundNumber" 
             class="round-column" :class="'round-' + round.roundNumber">
          <h3 class="column-label">{{ round.name }}</h3>
          <div v-for="series in round.series" :key="series.id" class="matchup-slot">
            <div class="matchup-content">
              <SeriesMatchup
                :series-data="series"
                :is-disabled="isSeriesVisuallyDisabled(series, round.roundNumber)"
                @pick-made="handlePick"
              />
              <div v-if="series.predicted_winner_team_id" class="length-selector">
                <span class="len-label">In:</span>
                <button v-for="n in [4,5,6,7]" :key="n"
                  :class="{ active: series.predicted_series_length === n }"
                  @click.stop="handleLengthPick(series.id, n)">{{ n }}</button>
              </div>
            </div>
          </div>
        </div>

        <div class="round-column round-final">
          <h3 class="column-label">Finals</h3>
          <div class="matchup-slot">
            <div v-if="stanleyCupFinalSeries" class="matchup-content scf-box">
              <SeriesMatchup
                :series-data="stanleyCupFinalSeries"
                :is-disabled="isSeriesVisuallyDisabled(stanleyCupFinalSeries, 4)"
                @pick-made="handlePick"
              />
              <div v-if="stanleyCupFinalSeries.predicted_winner_team_id" class="length-selector">
                <span class="len-label">Games:</span>
                <button v-for="n in [4,5,6,7]" :key="n"
                  :class="{ active: stanleyCupFinalSeries.predicted_series_length === n }"
                  @click.stop="handleLengthPick(stanleyCupFinalSeries.id, n)">{{ n }}</button>
              </div>
            </div>
          </div>
        </div>

        <div v-for="round in reversedEasternRounds" :key="'e'+round.roundNumber" 
             class="round-column" :class="'round-' + round.roundNumber">
          <h3 class="column-label">{{ round.name }}</h3>
          <div v-for="series in round.series" :key="series.id" class="matchup-slot">
            <div class="matchup-content">
              <SeriesMatchup
                :series-data="series"
                :is-disabled="isSeriesVisuallyDisabled(series, round.roundNumber)"
                @pick-made="handlePick"
              />
              <div v-if="series.predicted_winner_team_id" class="length-selector">
                <span class="len-label">In:</span>
                <button v-for="n in [4,5,6,7]" :key="n"
                  :class="{ active: series.predicted_series_length === n }"
                  @click.stop="handleLengthPick(series.id, n)">{{ n }}</button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>

    <footer class="bracket-footer">
      <button @click="attemptSubmitBracket" :disabled="!canSubmit" class="submit-btn">
        Submit 2026 Bracket
      </button>
      <div class="status-box">
        <p v-if="!canSubmit && localPlayerName" class="status-msg">
          {{ !allPicksComplete ? 'Complete all 15 picks + game lengths to submit' : '' }}
        </p>
      </div>
    </footer>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useBracketStore } from '@/stores/bracketStore';
import SeriesMatchup from './SeriesMatchup.vue';

const bracketStore = useBracketStore();
const currentYear = 2026;
const localPlayerName = ref(bracketStore.playerName);
const submitting = ref(false);

watch(localPlayerName, (val) => bracketStore.setPlayerName(val));

// DATA FETCHING
const createConfRounds = (pref: 'WC' | 'EC') => {
  return [1, 2, 3].map(num => ({
    roundNumber: num,
    name: num === 3 ? 'Conf. Finals' : num === 2 ? 'Semis' : 'Round 1',
    series: bracketStore.allSeries
      .filter(s => s.round_number === num && s.series_identifier.startsWith(pref))
      .sort((a,b) => a.series_identifier.localeCompare(b.series_identifier))
  }));
};

const westernConferenceRounds = computed(() => createConfRounds('WC'));
const easternConferenceRounds = computed(() => createConfRounds('EC'));
const reversedEasternRounds = computed(() => [...easternConferenceRounds.value].reverse());
const stanleyCupFinalSeries = computed(() => bracketStore.allSeries.find(s => s.round_number === 4));

// LOGIC
const handlePick = (id: number, winId: number | null) => bracketStore.makePick(id, winId);
const handleLengthPick = (id: number, len: number) => bracketStore.makePick(id, null, len);

const allPicksComplete = computed(() => {
  return bracketStore.allSeries.length > 0 && 
         bracketStore.allSeries.every(s => s.predicted_winner_team_id && s.predicted_series_length);
});

const canSubmit = computed(() => allPicksComplete.value && localPlayerName.value.trim() && !bracketStore.isLoading);

const isSeriesVisuallyDisabled = (series: any, round: number) => {
  return !series || series.status !== 'PENDING' || !series.team1_id || !series.team2_id;
};

const attemptSubmitBracket = async () => {
  submitting.value = true;
  await bracketStore.submitBracket();
  submitting.value = false;
};

const handleNameInput = () => { bracketStore.error = null; bracketStore.successMessage = null; };

onMounted(() => {
  bracketStore.fetchBracketStructure().then(() => bracketStore.fetchOfficialResults());
});
</script>

<style scoped>
.playoff-bracket-page {
  background: #f0f2f5;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow-x: hidden; /* Prevents body-level scrolling */
}

/* 1. HEADER (NHL Blue Bar) */
.bracket-header { 
  width: 100%; 
  background: #004786; /* NHL Blue */
  padding: 15px 0;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  display: flex;
  justify-content: center;
}
.header-content {
  max-width: 1200px;
  width: 100%;
  text-align: center;
}
.bracket-header h1 { 
  font-size: 1.8rem; 
  color: #ffffff; /* White Text */
  margin: 0 0 10px 0;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.controls input { 
  padding: 10px; 
  width: 280px; 
  border-radius: 6px; 
  border: none;
  font-size: 1rem;
  text-align: center;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}

/* 2. MESSAGES */
.message-area { min-height: 45px; margin-top: 10px; }
.message { padding: 8px 20px; border-radius: 4px; font-weight: bold; }
.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }

/* 3. BRACKET SCALING & FIT */
.bracket-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
  /* Slightly more aggressive scaling for horizontal fit */
  transform: scale(0.88); 
  transform-origin: top center;
  margin-bottom: -80px; 
}

.bracket-display {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 6px; /* Reduced gap from 10px */
}

.round-column {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  width: 155px; /* Reduced width from 170px to save horizontal space */
}

.column-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: #999;
  text-align: center;
  margin-bottom: 5px;
}

.matchup-slot {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 110px;
}

/* 4. LENGTH SELECTOR (Compact) */
.length-selector {
  margin-top: 4px;
  background: white;
  padding: 3px 6px;
  border-radius: 15px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid #ddd;
}
.len-label { font-size: 0.6rem; font-weight: bold; color: #bbb; }
.length-selector button {
  border: 1px solid #eee;
  background: #f9f9f9;
  border-radius: 50%;
  width: 22px; /* Tiny buttons for space */
  height: 22px;
  font-size: 0.7rem;
  cursor: pointer;
}
.length-selector button.active {
  background: #004786;
  color: white;
  border-color: #004786;
}

/* 5. FOOTER */
.bracket-footer {
  text-align: center;
  padding: 20px 0 40px 0;
  background: transparent;
}
.submit-btn {
  padding: 12px 45px;
  font-size: 1.1rem;
  font-weight: bold;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 30px;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(39, 174, 96, 0.3);
}
.submit-btn:disabled { background: #ccc; box-shadow: none; cursor: not-allowed; }
.status-box { height: 20px; margin-top: 10px; }
.status-msg { color: #888; font-size: 0.8rem; }
</style>