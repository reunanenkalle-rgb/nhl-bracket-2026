<template>
    <div 
      class="ro-series-matchup"
      :class="{
        'series-complete': series.series_status === 'COMPLETED',
        'pick-correct': series.is_pick_correct === true,
        'pick-incorrect': series.is_pick_correct === false
      }"
    >
      <div class="teams-stacked-ro">
        <div class="team-ro" 
             :class="{ 
               'picked-winner-ro': isPicked(series.series_team1_abbr), 
               'actual-winner-ro': isActualWinner(series.series_team1_abbr) && series.series_status === 'COMPLETED'
             }">
          <img v-if="series.series_team1_logo" :src="series.series_team1_logo" :alt="series.series_team1_abbr || 'T1'" class="team-logo-ro"/>
          <span class="team-abbr-ro">{{ series.series_team1_abbr || 'TBD' }}</span>
          <span v-if="series.series_status !== 'PENDING' && series.games_team1_won !== undefined && series.games_team1_won !== null && series.series_team1_abbr" class="series-score-ro">{{ series.games_team1_won }}</span>
        </div>
  
        <div class="vs-separator-ro">vs</div>
  
        <div class="team-ro" 
             :class="{ 
               'picked-winner-ro': isPicked(series.series_team2_abbr), 
               'actual-winner-ro': isActualWinner(series.series_team2_abbr) && series.series_status === 'COMPLETED'
             }">
          <img v-if="series.series_team2_logo" :src="series.series_team2_logo" :alt="series.series_team2_abbr || 'T2'" class="team-logo-ro"/>
          <span class="team-abbr-ro">{{ series.series_team2_abbr || 'TBD' }}</span>
          <span v-if="series.series_status !== 'PENDING' && series.games_team2_won !== undefined && series.games_team2_won !== null && series.series_team2_abbr" class="series-score-ro">{{ series.games_team2_won }}</span>
        </div>
      </div>
      
      <div class="pick-status">
          <div v-if="series.predicted_winner_abbr" class="user-pick-display">
              Picked: 
              <img v-if="series.predicted_winner_logo" :src="series.predicted_winner_logo" :alt="series.predicted_winner_abbr" class="team-logo-tiny"/>
              {{ series.predicted_winner_abbr }}
          </div>
          <div v-else class="user-pick-display">No pick made</div>
  
          <div v-if="series.series_status === 'COMPLETED'" class="pick-result-container">
              <span v-if="series.is_pick_correct === true" class="correct pick-result">&#10004; Correct</span>
              <span v-else-if="series.is_pick_correct === false" class="incorrect pick-result">&#10008; Incorrect</span>
              <span v-else class="pick-result">Outcome Known / No Pick</span>
          </div>
      </div>
    </div>
  </template>
  
  <script lang="ts" setup>
  import type { ViewedPickDetail } from '@/types';
  import { defineProps } from 'vue';
  
  const props = defineProps<{
    series: ViewedPickDetail;
    // Note: The isDisabled prop from interactive SeriesMatchup is not used here
    // as this component is purely for display. Disablement is handled by context.
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
    border: 1px solid #dcdcdc; /* Slightly lighter border */
    padding: 6px; /* Reduced padding further */
    border-radius: 5px; /* Slightly smaller radius */
    background-color: #fff;
    width: fit-content; 
    margin: 0 auto;     
    min-width: 140px;   /* TRY REDUCING: e.g., 140px or 150px */
    max-width: 160px;   /* TRY REDUCING: e.g., 160px or 170px */
    box-sizing: border-box;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    display: flex;
    flex-direction: column;
    justify-content: center; /* Should keep content centered vertically */
  }
  
  /* .series-info styles can be completely removed */
  
  .teams-stacked-ro {
    display: flex;
    flex-direction: column;
    align-items: center; 
    width: 100%;
    gap: 2px; /* Tighter gap */
  }
  
  .team-ro {
    display: flex;
    align-items: center;
    padding: 4px 6px; /* Reduced padding */
    border: 1px solid #e8e8e8; /* Lighter border for team items */
    border-radius: 3px;
    width: 100%; 
    box-sizing: border-box;
    background-color: #fff; 
    font-size: 0.8em; /* Smaller font for even more compactness */
    margin-bottom: 3px; /* From your working PlayoffBracket.vue */
  }
  .team-ro:last-child {
    margin-bottom: 0;
  }
  
  .team-logo-ro {
    width: 25px; /* Slightly smaller logo */
    height: 25px;
    margin-right: 5px;
    object-fit: contain;
    flex-shrink: 0;
  }
  .team-abbr-ro {
    flex-grow: 1; 
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 500; /* Slightly less bold than picked/winner states */
  }
  .series-score-ro {
    font-weight: bold;
    margin-left: 5px;
    padding-left: 5px;
    flex-shrink: 0;
    font-size: 0.95em;
  }
  .vs-separator-ro {
    font-size: 0.75em;
    color: #888; /* Lighter vs */
    margin: 1px 0;
    text-align: center;
    font-weight: 500;
  }
  
  .picked-winner-ro {
     box-shadow: inset 0 0 0 2px #007bff; /* Blue inset highlight for pick */
  }
  
  .actual-winner-ro { /* Style for the team div that was the actual winner */
    /* If a team is both picked and actual winner, it will have both box-shadow and this font-weight */
    font-weight: bold !important; /* Make actual winner text bold */
  }
  
  /* Combined styles for visual feedback on pick correctness */
  .ro-series-matchup.pick-correct .team-ro.picked-winner-ro {
    background-color: #d1e7dd; /* Light green background if pick was correct */
    border-color: #28a745;
  }
  .ro-series-matchup.pick-incorrect .team-ro.picked-winner-ro {
     background-color: #f8d7da; /* Light red background if pick was incorrect */
     border-color: #dc3545;
     /* text-decoration: line-through; */ /* Optional: strike-through for incorrect pick's text */
  }
  .ro-series-matchup.pick-incorrect .team-ro.picked-winner-ro .team-abbr-ro {
      text-decoration: line-through; /* Strike-through only the abbreviation */
  }
  
  
  .pick-status {
    margin-top: 5px; /* Reduced margin */
    font-size: 0.75em; /* Smaller status text */
    text-align: center;
  }
  .user-pick-display {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 3px;
      margin-bottom: 2px; /* Reduced margin */
      color: #444; /* Slightly darker */
  }
  .team-logo-tiny {
      width: 12px; /* Smaller logo in status */
      height: 12px;
      object-fit: contain;
  }
  .pick-result-container { /* Container for Correct/Incorrect text */
      margin-top: 2px;
  }
  .pick-result { 
      font-weight: bold;
  }
  .correct {
    color: #155724; 
  }
  .incorrect {
    color: #842029; 
  }
  .series-complete {
    /* No specific style needed if individual elements handle appearance */
  }
  </style>