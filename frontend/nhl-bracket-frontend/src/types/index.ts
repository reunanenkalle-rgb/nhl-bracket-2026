// frontend/src/types/index.ts

export interface Player {
  id: number;
  name: string;
}

// For displaying detailed team info (e.g., if you had a dedicated teams page/list)
export interface Team {
  id: number;
  nhl_api_id: number;
  name: string;
  abbreviation: string;
  conference: string | null;
  logo_url: string | null;
}

// A shorter version of team details, often embedded in other objects like Series from API
export interface TeamShort {
  id: number | null;
  name: string | null;
  abbreviation: string | null; // Used to be 'abbr' in some examples, standardizing to 'abbreviation'
  logo_url: string | null;     // Used to be 'logo' in some examples, standardizing to 'logo_url'
}

export interface Series {
  id: number;
  round_number: number;
  series_identifier: string;
  description: string;
  status: string; // e.g., 'PENDING', 'ACTIVE', 'COMPLETED'

  // Team 1 details as received from API (populated by backend)
  team1_id: number | null;
  team1_name: string | null;
  team1_abbr: string | null;   // Standardize to team1_abbr from API
  team1_logo: string | null;   // Standardize to team1_logo from API

  // Team 2 details as received from API (populated by backend)
  team2_id: number | null;
  team2_name: string | null;
  team2_abbr: string | null;   // Standardize to team2_abbr from API
  team2_logo: string | null;   // Standardize to team2_logo from API

  actual_winner_team_id: number | null;
  games_team1_won?: number; // Optional, might not be there initially
  games_team2_won?: number; // Optional

  // For UI state, managed by Pinia store; this is the user's pick for this series
  predicted_winner_team_id?: number | null;
}

// Type for an individual pick when constructing the submission payload
export interface PickPayload { // This replaces the 'Pick' that was aliased to 'UserPick'
  series_id: number;
  predicted_winner_team_id: number;
}

// Type for the entire bracket submission payload sent to the API
export interface BracketSubmissionApiPayload {
  player_name: string;
  picks: PickPayload[]; // Uses PickPayload for the array of picks
}

// Type for the response from the backend after successful submission (example)
export interface BracketSubmissionApiResponse {
  message: string;
  submission_id: number;
  // You might also include the full submitted bracket details if backend returns them
}

export interface LeaderboardEntry {
  submission_id: number;
  player_name: string;
  score: number;
  percentage_correct: number;
  correct_picks: number;
  completed_series: number;
  stanley_cup_pick_abbr: string | null;
  stanley_cup_pick_logo_url: string | null;
}

export interface ViewedPickDetail {
  series_id: number;
  series_identifier: string;
  description: string;
  round_number: number;
  
  series_team1_abbr: string | null;
  series_team1_logo: string | null;
  series_team2_abbr: string | null;
  series_team2_logo: string | null;
  
  predicted_winner_team_id: number | null;
  predicted_winner_abbr: string | null;
  predicted_winner_logo: string | null;
  
  actual_winner_team_id: number | null;
  actual_winner_abbr: string | null;
  actual_winner_logo: string | null;
  
  games_team1_won?: number;
  games_team2_won?: number;
  series_status: string; // e.g., 'PENDING', 'ACTIVE', 'COMPLETED'
  is_pick_correct: boolean | null; // true, false, or null if series not completed or no pick
}

export interface DetailedBracketView {
  submission_id: number;
  player_name: string;
  bracket_name: string | null;
  submission_timestamp: string | null; // ISO date string
  score: number;
  // You might also get these from the leaderboard endpoint or calculate on front-end based on picks
  // percentage_correct?: number; 
  // correct_picks?: number;
  // completed_series?: number;
  picks: ViewedPickDetail[]; // Array of all picks with series info and results
}