<template>
  <div 
    class="series-matchup" 
    :class="{ 
      'series-complete': seriesData.status === 'COMPLETED',
      'visually-disabled': isDisabled  // Overall visual cue if the whole matchup is disabled
    }"
  >
    <div class="teams-stacked">
      <div
        class="team team-one"
        :class="{
          'pickable': canPickTeam1 && !isDisabled,
          'picked-winner': isTeamPicked(seriesData.team1_id),
          'actual-winner': isActualWinner(seriesData.team1_id),
          'team-tbd': !seriesData.team1_id
        }"
        @click="selectWinner(seriesData.team1_id)"
      >
        <img v-if="seriesData.team1_logo" :src="seriesData.team1_logo" :alt="seriesData.team1_abbr || ''" class="team-logo"/>
        <span>{{ seriesData.team1_abbr || 'TBD' }}</span>
        <span v-if="seriesData.games_team1_won !== undefined && seriesData.games_team1_won !== null && seriesData.team1_id" class="series-score">
          {{ seriesData.games_team1_won }}
        </span>
      </div>

      <div class="vs-separator">vs</div>

      <div
        class="team team-two"
        :class="{
          'pickable': canPickTeam2 && !isDisabled,
          'picked-winner': isTeamPicked(seriesData.team2_id),
          'actual-winner': isActualWinner(seriesData.team2_id),
          'team-tbd': !seriesData.team2_id
        }"
        @click="selectWinner(seriesData.team2_id)"
      >
         <img v-if="seriesData.team2_logo" :src="seriesData.team2_logo" :alt="seriesData.team2_abbr || ''" class="team-logo"/>
        <span>{{ seriesData.team2_abbr || 'TBD' }}</span>
         <span v-if="seriesData.games_team2_won !== undefined && seriesData.games_team2_won !== null && seriesData.team2_id" class="series-score">
          {{ seriesData.games_team2_won }}
        </span>
      </div>
    </div>

    <div v-if="seriesData.status === 'COMPLETED' && seriesData.actual_winner_team_id && (seriesData.team1_abbr || seriesData.team2_abbr)" class="series-result">
      </div>
  </div>
</template>

<script lang="ts" setup>
import type { Series } from '@/types';
import { defineProps, defineEmits, computed } from 'vue';

const props = defineProps<{
  seriesData: Series;
  isDisabled?: boolean; // Passed from PlayoffBracket.vue for round locking
}>();

const emit = defineEmits<{
  (e: 'pick-made', seriesId: number, winningTeamId: number | null): void;
}>();

// A team slot is pickable if the series is pending, the team exists, and the matchup itself isn't disabled
const canPickTeam1 = computed(() => props.seriesData.status === 'PENDING' && props.seriesData.team1_id !== null);
const canPickTeam2 = computed(() => props.seriesData.status === 'PENDING' && props.seriesData.team2_id !== null);

const selectWinner = (teamId: number | null) => {
  if (props.isDisabled) return; // If the whole matchup is disabled (e.g., previous round not complete)

  // Determine if the specific team clicked is pickable (i.e., not TBD)
  const clickedTeamIsPickable = (teamId === props.seriesData.team1_id && canPickTeam1.value) || 
                                (teamId === props.seriesData.team2_id && canPickTeam2.value);

  if (props.seriesData.status !== 'PENDING' || !teamId || !clickedTeamIsPickable) {
    // Allow un-picking by clicking the currently picked winner, even if one slot is TBD (but the picked one is not)
    if (props.seriesData.predicted_winner_team_id === teamId && teamId !== null) {
       emit('pick-made', props.seriesData.id, null);
    }
    return;
  }

  if (props.seriesData.predicted_winner_team_id === teamId) {
    emit('pick-made', props.seriesData.id, null); // Un-pick if clicking the same winner
  } else {
    emit('pick-made', props.seriesData.id, teamId); // Pick the new winner
  }
};

const isTeamPicked = (teamId: number | null) => {
  return teamId !== null && props.seriesData.predicted_winner_team_id === teamId;
};

const isActualWinner = (teamId: number | null) => {
  return teamId !== null && props.seriesData.actual_winner_team_id === teamId;
};
</script>

<style scoped>
.series-matchup {
  border: 1px solid #d0d0d0; /* Slightly more prominent border */
  padding: 8px; /* Uniform padding */
  border-radius: 6px;
  /*width: 100%; /* Takes width of its container in round-column */
  width: fit-content;
  margin: 0 auto;
  min-width: 150px; /* Minimum width for better scaling */
  max-width: 180px; /* Maximum width to keep it compact */
  box-sizing: border-box;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.06);
  display: flex; /* To help center series-result if needed */
  flex-direction: column;
  justify-content: center; /* Center content vertically */
}

.series-matchup.visually-disabled {
  opacity: 0.7;
  background-color: #f8f9fa;
}
.series-matchup.visually-disabled .team {
  cursor: default;
}


.teams-stacked {
  display: flex;
  flex-direction: column;
  align-items: center; /* Center teams and 'vs' text */
  width: 100%;
  gap: 4px; /* Space between teams */
}

.team {
  display: flex;
  align-items: center;
  /* justify-content: space-between; */ /* Let content determine width within padding */
  gap: 6px; /* Space between logo and team name */
  padding: 6px 8px; /* Slightly reduced padding */
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  /*width: 100%; /* Team takes full width of its parent (.teams-stacked) */
  width: fit-content;
  min-width: 120px;
  max-width: 100%;
  box-sizing: border-box;
  margin-bottom: 4px; /* Space below team before 'vs' or next team */
  transition: background-color 0.2s ease, border-color 0.2s ease;
  font-size: 0.9em; /* Slightly smaller font for team names */
  justify-content: flex-start;
}
.team:last-child {
  margin-bottom: 0;
}

.team.pickable:not(.team-tbd) { /* Only truly pickable teams get hover/cursor */
  cursor: pointer;
}
.team.pickable:not(.team-tbd):hover {
  background-color: #f1f3f5; /* Lighter hover */
  border-color: #adb5bd;
}

.team.team-tbd {
  color: #6c757d; /* Grey out TBD text */
  justify-content: center; /* Center TBD text if no logo */
  font-style: italic;
}

.series-matchup.visually-disabled .team.pickable:not(.team-tbd) {
  cursor: default; /* No pointer if whole matchup is disabled */
}
.series-matchup.visually-disabled .team.pickable:not(.team-tbd):hover {
  background-color: transparent; /* No hover effect if disabled */
  border-color: #e0e0e0;
}


.team.picked-winner {
  background-color: #d1e7dd; /* Softer green for picked */
  border-color: #28a745;
  font-weight: 600; /* Bold for picked */
  color: #0f5132;
}

.team.actual-winner {
  /* If you want a distinct style for actual winners that overrides/combines */
  /* For example, a thicker border or a small icon */
  /* border-left: 3px solid gold !important; */ /* Important might be needed to override other borders */
}

.team-logo {
  width: 22px;
  height: 22px;
  margin-right: 8px;
  object-fit: contain;
}

.vs-separator {
  font-weight: 600;
  color: #495057; /* Darker grey */
  font-size: 0.85em;
  margin: 3px 0; /* Tighter margin */
  text-align: center;
}

.series-score {
  font-size: 0.9em;
  color: #212529; /* Darker score text */
  margin-left: auto; /* Pushes score to the right */
  padding-left: 8px;
  font-weight: 600;
}

.series-result {
  text-align: center;
  font-weight: bold;
  margin-top: 8px;
  font-size: 0.9em;
  color: #198754; /* Bootstrap success green for winner text */
}

.series-complete {
  background-color: #f7f7f9;
  border-color: #ced4da;
}
</style>