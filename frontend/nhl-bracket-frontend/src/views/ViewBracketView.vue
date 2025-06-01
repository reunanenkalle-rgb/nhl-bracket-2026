<template>
  <div class="view-bracket-page">
    <div v-if="store.isLoadingViewedBracket" class="message loading-message">Loading bracket details...</div>
    <div v-if="!store.isLoadingViewedBracket && store.error" class="message error-message">{{ store.error }}</div>
    
    <div v-if="bracketData" class="bracket-details-content">
      <div class="bracket-header">
        <h2>{{ bracketData.player_name }}'s Bracket
          <span v-if="bracketData.bracket_name">({{ bracketData.bracket_name }})</span>
        </h2>
        <p class="bracket-subtitle">
          Score: <span class="score-value">{{ bracketData.score }}</span> |
          Correct Picks: <span class="score-value">{{ bracketData.correct_picks_count }} / {{ bracketData.total_completed_series_count }}</span> 
          ({{ bracketData.percentage_correct }}%)
          <br v-if="bracketData.submission_timestamp"> <span v-if="bracketData.submission_timestamp">Submitted: {{ formatTimestamp(bracketData.submission_timestamp) }}</span>
        </p>
      </div>

      <div class="bracket-container-ro">
        <div class="conference-bracket-ro west-conference-ro">
          <div v-for="round in westernConferenceRounds" :key="'wc-r'+round.roundNumber" 
               class="round-column-ro" :class="`round-${round.roundNumber}`">
            <h3 class="round-title-ro">{{ round.name }}</h3>
            <ReadOnlySeriesMatchup
              v-for="series in round.series"
              :key="series.series_identifier"
              :series="series"
            />
          </div>
        </div>

        <div class="final-column-ro round-column-ro round-4">
           <h3 class="round-title-ro">{{ stanleyCupFinalRoundInfo.name }}</h3>
          <ReadOnlySeriesMatchup
            v-if="stanleyCupFinalSeries"
            :key="stanleyCupFinalSeries.series_identifier"
            :series="stanleyCupFinalSeries"
          />
        </div>

        <div class="conference-bracket-ro east-conference-ro">
          <div v-for="round in easternConferenceRounds" :key="'ec-r'+round.roundNumber" 
               class="round-column-ro" :class="`round-${round.roundNumber}`">
            <h3 class="round-title-ro">{{ round.name }}</h3>
            <ReadOnlySeriesMatchup
              v-for="series in round.series"
              :key="series.series_identifier"
              :series="series"
            />
          </div>
        </div>
      </div>
      <RouterLink to="/leaderboard" class="back-link">Back to Leaderboard</RouterLink>
    </div>
    <div v-else-if="!store.isLoadingViewedBracket && !bracketData">
        <p class="message info-message">Could not load bracket details.</p>
        <RouterLink to="/leaderboard" class="back-link">Back to Leaderboard</RouterLink>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, computed } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import { useBracketStore } from '@/stores/bracketStore';
import ReadOnlySeriesMatchup from '@/components/ReadOnlySeriesMatchup.vue'; // Path to your new component
import type { ViewedPickDetail } from '@/types';

const store = useBracketStore();
const route = useRoute();

const bracketData = computed(() => store.viewedBracket);

const roundNames: Record<number, string> = {
  1: 'Round 1', 2: 'Conference Semifinals', 3: 'Conference Finals', 4: 'Stanley Cup Final',
};

const formatTimestamp = (timestamp: string | null): string => {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleString();
};

// Helper to group and sort series for display (similar to PlayoffBracket.vue)
const createConferenceRoundsForView = (conferencePrefix: 'EC' | 'WC', allPicks: ViewedPickDetail[]) => {
  const roundsOutput = [];
  for (let i = 1; i <= 3; i++) {
    const seriesForRound = allPicks
      .filter(p => p.round_number === i && p.series_identifier.startsWith(conferencePrefix))
      .sort((a, b) => a.series_identifier.localeCompare(b.series_identifier));
    if (seriesForRound.length > 0 || i <= 3) { // Ensure column exists for layout
      roundsOutput.push({ roundNumber: i, name: roundNames[i], series: seriesForRound });
    }
  }
  return roundsOutput;
};

const westernConferenceRounds = computed(() => 
  bracketData.value ? createConferenceRoundsForView('WC', bracketData.value.picks) : []
);
const easternConferenceRounds = computed(() => 
  bracketData.value ? createConferenceRoundsForView('EC', bracketData.value.picks) : []
);
const stanleyCupFinalSeries = computed(() => 
  bracketData.value?.picks.find(p => p.round_number === 4 && p.series_identifier === 'SCF')
);
const stanleyCupFinalRoundInfo = computed(() => ({
  roundNumber: 4, name: roundNames[4],
}));

onMounted(() => {
  const submissionIdParam = route.params.submissionId;
  if (submissionIdParam) {
    const id = Array.isArray(submissionIdParam) ? submissionIdParam[0] : submissionIdParam;
    store.fetchSubmissionDetails(id);
  }
});
</script>

<style scoped>
.view-bracket-page { padding: 20px; }
.bracket-header { text-align: center; margin-bottom: 25px; }
.bracket-header h2 { margin-bottom: 5px; }
.bracket-subtitle { font-size: 1.1em; color: #555; }
.score { font-weight: bold; color: #007bff; }

.bracket-container-ro {
  display: flex;
  justify-content: space-center; /* Or 'center' if you prefer less spread */
  align-items: flex-start;
  overflow-x: auto;
  padding: 1px 0; 
  gap: 1px; /* HORIZONTAL gap between [West], [Final], [East] sections */
}
.conference-bracket-ro {
  display: flex;
  gap: 1px; /* HORIZONTAL gap between round columns */
}
.east-conference-ro { flex-direction: row-reverse; }

.round-column-ro {
  display: flex;
  flex-direction: column;
  align-items: center; /* This will center the 'fit-content' ro-series-matchup boxes */
  gap: 15px; /* VERTICAL gap between ReadOnlySeriesMatchup. Was 10px, maybe a bit more now */
  padding: 0 2px;
  min-width: auto; /* Let the content define width as much as possible */
  /* You might set a min-width if needed, e.g., min-width: 200px; based on new ro-series-matchup width */
}
.round-title-ro {
  margin-bottom: 10px;
  text-align: center;
  font-size: 1em;
  color: #333;
  font-weight: 600;
  max-width: 160px; /* Ensure it fits */
  line-height: 1.2;
  word-wrap: break-word;
}

/* Vertical alignment - these will need the most tweaking based on final ReadOnlySeriesMatchup height */
.round-column-ro.round-2 { padding-top: 156px; /* Adjust these! */ }
.round-column-ro.round-3 { padding-top: 250px; /* Adjust these! */ }
.final-column-ro.round-4 { 
  padding-top: 250px; /* Try to align with R3 */
  min-width: 200px; /* Was 220px, can probably be narrower now */
}

.message { /* Copied from PlayoffBracket for consistency */
  padding: 12px 15px; margin: 15px auto; max-width: 80%;
  border-radius: 5px; text-align: center; font-size: 0.95em; border: 1px solid transparent;
}
.loading-message { background-color: #e9ecef; color: #495057; border-color: #ced4da; }
.error-message { background-color: #f8d7da; color: #842029; border-color: #f5c2c7; }
.info-message { background-color: #cce5ff; color: #004085; border-color: #b8daff; }

.back-link {
    display: inline-block;
    margin-top: 25px;
    padding: 8px 15px;
    background-color: #6c757d;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    transition: background-color 0.2s ease;
}
.back-link:hover {
    background-color: #5a6268;
}
.bracket-header { text-align: center; margin-bottom: 25px; }
.bracket-header h2 { margin-bottom: 5px; color: #333; }
.bracket-subtitle { 
    font-size: 1rem; /* Adjusted size */
    color: #555; 
    line-height: 1.5; /* For multi-line readability */
}
.score-value { 
    font-weight: bold; 
    color: #007bff; /* Or your theme color */
}

</style>