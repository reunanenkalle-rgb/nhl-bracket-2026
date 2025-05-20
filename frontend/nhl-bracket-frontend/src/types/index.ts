export interface Team {
    id: number;
    name: string;
    abbreviation: string;
    conference: string;
    // logo_url?: string;
  }
  
  export interface Player {
    id: number;
    name: string;
  }
  
  export interface Pick {
    id?: number; // Optional if it's a new pick not yet saved
    series_identifier: string;
    predicted_winner_team_id: number;
  }
  
  export interface BracketSubmission {
    id?: number; // Optional for new submissions
    bracket_name: string;
    player_id: number; // Or perhaps the Player object itself
    picks: Pick[];
    // timestamp_submitted?: string; // Or Date object
  }