<template>
    <div class="series-matchup" :class="{ 'series-complete': seriesData.status === 'COMPLETED' }">
      <div class="series-description">{{ seriesData.description }} ({{seriesData.series_identifier}})</div>
      <div class="teams">
        <div
          class="team team-one"
          :class="{
            'pickable': canPickTeam1,
            'picked-winner': isTeamPicked(seriesData.team1_id),
            'actual-winner': isActualWinner(seriesData.team1_id),
            'disabled': !canPickTeam1
          }"
          @click="selectWinner(seriesData.team1_id)"
        >
          <img v-if="seriesData.team1_logo" :src="seriesData.team1_logo" :alt="seriesData.team1_abbr || ''" class="team-logo"/>
          <span>{{ seriesData.team1_abbr || 'TBD' }}</span>
          <span v-if="seriesData.games_team1_won !== undefined && seriesData.games_team1_won !== null" class="series-score">
            {{ seriesData.games_team1_won }}
          </span>
        </div>
        <div class="vs">vs</div>
        <div
          class="team team-two"
          :class="{
            'pickable': canPickTeam2,
            'picked-winner': isTeamPicked(seriesData.team2_id),
            'actual-winner': isActualWinner(seriesData.team2_id),
            'disabled': !canPickTeam2
          }"
          @click="selectWinner(seriesData.team2_id)"
        >
           <img v-if="seriesData.team2_logo" :src="seriesData.team2_logo" :alt="seriesData.team2_abbr || ''" class="team-logo"/>
          <span>{{ seriesData.team2_abbr || 'TBD' }}</span>
           <span v-if="seriesData.games_team2_won !== undefined && seriesData.games_team2_won !== null" class="series-score">
            {{ seriesData.games_team2_won }}
          </span>
        </div>
      </div>
      <div v-if="seriesData.status === 'COMPLETED' && seriesData.actual_winner_team_id && (seriesData.team1_abbr || seriesData.team2_abbr)" class="series-result">
        Winner: {{ seriesData.actual_winner_team_id === seriesData.team1_id ? seriesData.team1_abbr : seriesData.team2_abbr }}
      </div>
    </div>
  </template>
  
  <script lang="ts" setup>
  import type { Series } from '@/types'; // Ensure your types path is correct
  import { defineProps, defineEmits, computed } from 'vue';
  
  const props = defineProps<{
    seriesData: Series;
    isDisabled?: boolean; // New Prop
  }>();
  
  const emit = defineEmits<{
    (e: 'pick-made', seriesId: number, winningTeamId: number | null): void;
  }>();
  
  const canPickTeam1 = computed(() => props.seriesData.status === 'PENDING' && props.seriesData.team1_id !== null);
  const canPickTeam2 = computed(() => props.seriesData.status === 'PENDING' && props.seriesData.team2_id !== null);
  
  const selectWinner = (teamId: number | null) => {
    if (props.isDisabled) return;
    if (props.seriesData.status !== 'PENDING' || !teamId) {
      // If already picked, allow un-picking by clicking the picked team again
      if (props.seriesData.predicted_winner_team_id === teamId && teamId !== null) {
         emit('pick-made', props.seriesData.id, null);
      }
      return;
    }
  
    // If already picked this team, un-pick it. Otherwise, pick it.
    if (props.seriesData.predicted_winner_team_id === teamId) {
      emit('pick-made', props.seriesData.id, null);
    } else {
      emit('pick-made', props.seriesData.id, teamId);
    }
  };
  
  const isTeamPicked = (teamId: number | null) => {
    return teamId !== null && props.seriesData.predicted_winner_team_id === teamId;
  };
  
  const isActualWinner = (teamId: number | null) => {
    return teamId !== null && props.seriesData.actual_winner_team_id === teamId;
  }
  </script>
  
  <style scoped>
  .series-matchup {
    border: 1px solid #e0e0e0;
    padding: 10px 12px;
    margin-bottom: 10px;
    border-radius: 6px;
    width: 100%;
    box-sizing: border-box;
    background-color: #fff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  .series-description {
    font-size: 0.75em; /* Smaller */
    color: #666; /* Lighter */
    margin-bottom: 8px;
    text-align: center;
    font-weight: 500;
  }
  .teams {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .team {
    padding: 8px 10px;
    border: 1px solid #d0d0d0; /* Default border */
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
    flex-grow: 1; /* Allow teams to grow */
    justify-content: flex-start; /* Align content to start */
    transition: background-color 0.2s ease, border-color 0.2s ease;
  }
  .team.pickable {
    cursor: pointer;
  }
  .team.pickable:hover {
    background-color: #f5f5f5;
    border-color: #b0b0b0;
  }
  .team.disabled {
    cursor: default;
    opacity: 0.7;
    background-color: #f9f9f9;
  }
  .team.picked-winner {
    background-color: #e6ffed; /* Softer green */
    border-color: #28a745; /* Green border */
    font-weight: bold;
    color: #155724; /* Darker green text */
  }
  .team.actual-winner {
    /* Could add distinct style or combine. For now, picked-winner takes precedence if also picked. */
    border-left: 4px solid gold; /* Example: gold bar for actual winner */
  }
  .team-logo {
    width: 20px; /* Smaller */
    height: 20px;
    margin-right: 4px; /* Adjusted */
    object-fit: contain; /* Prevents squishing if not square */
  }
  .vs {
    font-weight: bold;
    margin: 0 8px; /* Adjusted */
    color: #555;
  }
  .series-score {
    font-size: 0.85em; /* Smaller */
    color: #333;
    margin-left: auto;
    padding-left: 8px;
    font-weight: 600;
  }
  .series-result {
    text-align: center;
    font-weight: bold;
    margin-top: 8px;
    font-size: 0.9em;
    color: #155724; /* Green for winner */
  }
  .series-complete {
    background-color: #f7f7f7; /* Slightly different background for completed series */
  }
  .series-matchup.disabled-true .team { /* Example: more visual cue for disabled */
  opacity: 0.6;
  pointer-events: none; /* Disables click if you don't handle it in script */
  background-color: #f0f0f0;
}
  </style>