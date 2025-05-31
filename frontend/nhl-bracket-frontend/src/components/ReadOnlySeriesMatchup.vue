<template>
    <div 
      class="ro-series-matchup"
      :class="{
        'series-complete': series.series_status === 'COMPLETED',
        'pick-correct': series.is_pick_correct === true,
        'pick-incorrect': series.is_pick_correct === false
      }"
    >
      <div class="series-info">
        <span class="round-info">R{{ series.round_number }}</span>
        <span class="series-desc">{{ series.description }}</span>
      </div>
  
      <div class="teams-stacked-ro">
        <div class="team-ro" :class="{ 'picked-winner-ro': isPicked(series.series_team1_abbr), 'actual-winner-ro': isActualWinner(series.series_team1_abbr) }">
          <img v-if="series.series_team1_logo" :src="series.series_team1_logo" :alt="series.series_team1_abbr || 'T1'" class="team-logo-ro"/>
          <span class="team-abbr-ro">{{ series.series_team1_abbr || 'TBD' }}</span>
          <span v-if="series.series_status !== 'PENDING' && series.games_team1_won !== undefined" class="series-score-ro">{{ series.games_team1_won }}</span>
        </div>
  
        <div class="vs-separator-ro">vs</div>
  
        <div class="team-ro" :class="{ 'picked-winner-ro': isPicked(series.series_team2_abbr), 'actual-winner-ro': isActualWinner(series.series_team2_abbr) }">
          <img v-if="series.series_team2_logo" :src="series.series_team2_logo" :alt="series.series_team2_abbr || 'T2'" class="team-logo-ro"/>
          <span class="team-abbr-ro">{{ series.series_team2_abbr || 'TBD' }}</span>
          <span v-if="series.series_status !== 'PENDING' && series.games_team2_won !== undefined" class="series-score-ro">{{ series.games_team2_won }}</span>
        </div>
      </div>
      
      <div class="pick-status">
          <div v-if="series.predicted_winner_abbr" class="user-pick-display">
              Your Pick: 
              <img v-if="series.predicted_winner_logo" :src="series.predicted_winner_logo" :alt="series.predicted_winner_abbr" class="team-logo-tiny"/>
              {{ series.predicted_winner_abbr }}
          </div>
          <div v-else class="user-pick-display">No pick made</div>
  
          <div v-if="series.series_status === 'COMPLETED'">
              <span v-if="series.is_pick_correct === true" class="correct">&#10004; Correct</span>
              <span v-else-if="series.is_pick_correct === false" class="incorrect">&#10008; Incorrect</span>
          </div>
      </div>
  
    </div>
  </template>
  
  <script lang="ts" setup>
  import type { ViewedPickDetail } from '@/types'; // This contains all the necessary fields
  import { defineProps, computed } from 'vue';
  
  const props = defineProps<{
    series: ViewedPickDetail;
  }>();
  
  const isPicked = (teamAbbr: string | null) => {
    return teamAbbr !== null && props.series.predicted_winner_abbr === teamAbbr;
  };
  
  const isActualWinner = (teamAbbr: string | null) => {
    return teamAbbr !== null && props.series.actual_winner_abbr === teamAbbr && props.series.series_status === 'COMPLETED';
  };
  </script>
  
  <style scoped>
  .ro-series-matchup {
    border: 1px solid #ccc;
    padding: 8px;
    border-radius: 6px;
    background-color: #f9f9f9;
    width: 100%;
    min-width: 200px;
    max-width: 240px; /* Matchup box width */
    box-sizing: border-box;
    margin-bottom: 5px; /* For vertical stacking in ViewBracketView */
  }
  .series-info {
    font-size: 0.75em;
    color: #555;
    margin-bottom: 6px;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .round-info {
    font-weight: bold;
    margin-right: 5px;
  }
  .teams-stacked-ro {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }
  .team-ro {
    display: flex;
    align-items: center;
    width: 100%;
    padding: 5px;
    border: 1px solid #eee;
    border-radius: 4px;
    background-color: #fff;
    font-size: 0.9em;
  }
  .team-logo-ro {
    width: 20px;
    height: 20px;
    margin-right: 6px;
    object-fit: contain;
  }
  .team-abbr-ro {
    flex-grow: 1;
  }
  .series-score-ro {
    font-weight: bold;
    margin-left: 8px;
  }
  .vs-separator-ro {
    font-size: 0.8em;
    color: #777;
    margin: 2px 0;
  }
  .picked-winner-ro {
    outline: 2px solid #007bff; /* Blue outline for user's pick */
    /* background-color: #e7f3ff; */
  }
  .actual-winner-ro {
    /* This class applies to the actual winning team in the list */
    /* We can use the pick-status div for more explicit Correct/Incorrect */
    font-weight: bold; /* Make actual winner bold */
  }
  
  .pick-status {
    margin-top: 8px;
    font-size: 0.85em;
    text-align: center;
  }
  .user-pick-display {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      margin-bottom: 4px;
  }
  .team-logo-tiny {
      width: 16px;
      height: 16px;
      object-fit: contain;
  }
  .correct {
    color: #28a745; /* Green */
    font-weight: bold;
  }
  .incorrect {
    color: #dc3545; /* Red */
    font-weight: bold;
  }
  .series-complete.pick-correct .user-pick-display {
    /* Optional: if you want specific style when overall pick is correct */
  }
  .series-complete.pick-incorrect .user-pick-display {
   /* Optional: if you want specific style when overall pick is incorrect */
  }
  </style>