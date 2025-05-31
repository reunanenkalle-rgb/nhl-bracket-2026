// frontend/src/stores/bracketStore.ts

import { defineStore } from 'pinia';
// Corrected imports from '@/types'
import type {
    Series,
    TeamShort,                // Now correctly defined and imported
    PickPayload,              // Import PickPayload for individual picks
    BracketSubmissionApiPayload, // Import the payload type for API submission
    LeaderboardEntry,
    DetailedBracketView
} from '@/types';
import apiService from '@/services/apiService';
import { progressionMap } from '@/bracketLogic/progressionMap';

// Helper type for team details needed for propagation within the store
// Its properties should match the team detail properties in the Series interface
interface AdvancingTeamDetails {
  id: number | null;
  name: string | null;
  abbr: string | null;   // Corresponds to teamX_abbr in Series
  logo: string | null;   // Corresponds to teamX_logo in Series
}

export interface BracketState {
  allSeries: Series[];
  originalSeriesData: Readonly<Series[]>; // For initial structure
  userPicks: Map<number, number | null>;
  playerName: string;
  isLoading: boolean;
  isLoadingResults: boolean; // New: for loading official results specifically
  error: string | null;
  successMessage: string | null; // From previous step
  isBracketCompletelyPicked: boolean;
  leaderboard: LeaderboardEntry[];
  isLoadingLeaderboard: boolean;
  viewedBracket: DetailedBracketView | null;
  isLoadingViewedBracket: boolean;
  // lastResultsFetchTimestamp: number | null; // Optional: to avoid over-fetching
}

export const useBracketStore = defineStore('bracket', {
  state: (): BracketState => ({
    allSeries: [],
    originalSeriesData: [],
    userPicks: new Map(),
    playerName: '',
    isLoading: false,
    isLoadingResults: false, // New: for loading official results specifically
    error: null,
    isBracketCompletelyPicked: false,
    successMessage: null, // Initialize successMessage
    leaderboard: [],
    isLoadingLeaderboard: false,
    viewedBracket: null,
    isLoadingViewedBracket: false,
  }),

  getters: {
    getSeriesById: (state) => (seriesId: number) => {
      return state.allSeries.find(s => s.id === seriesId);
    },
    isRoundFullyPicked: (state) => (roundNumber: number) => {
      const seriesInRound = state.allSeries.filter(s => s.round_number === roundNumber);
      // Ensure seriesInRound has teams to pick from before checking picks
      return seriesInRound.length > 0 && seriesInRound.every(s => 
        (s.team1_id !== null && s.team2_id !== null) && // Both teams must be set
        state.userPicks.has(s.id) && state.userPicks.get(s.id) !== null
      );
    },
    canAdvanceToRound: (state) => (roundNumber: number) => {
      if (roundNumber === 1) return true;
      // Check if all series in the *previous* round that have defined matchups are fully picked
      const prevRoundSeriesWithMatchups = state.allSeries.filter(s => 
        s.round_number === roundNumber - 1 && 
        s.team1_id !== null && 
        s.team2_id !== null
      );
      if (prevRoundSeriesWithMatchups.length === 0 && roundNumber > 1) { 
          // If previous round has no matchups yet (e.g. R2 waiting for R1), then cannot advance.
          // Exception: if R1 is empty, this condition itself might be tricky.
          // This assumes R1 will eventually have matchups from fetch.
          const prevRoundOriginalSeries = state.originalSeriesData.filter(s => s.round_number === roundNumber -1);
          if(prevRoundOriginalSeries.every(s => !s.team1_id || !s.team2_id)) return false; // No initial matchups to pick from
      }
      
      return prevRoundSeriesWithMatchups.every(s =>
        state.userPicks.has(s.id) && state.userPicks.get(s.id) !== null
      );
    },
  },

  actions: {
    async fetchBracketStructure() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await apiService.getPlayoffBracketStructure();
        const seriesFromAPI = response.data;
        
        // Deep immutable copy for original data
        this.originalSeriesData = Object.freeze(JSON.parse(JSON.stringify(seriesFromAPI)));
        
        // Initialize allSeries and userPicks
        this.allSeries = seriesFromAPI.map(s => ({
          ...s,
          predicted_winner_team_id: null,
        }));
        this.userPicks.clear();
        
        this.updateAdvancingTeams(); // Initial call to set up TBDs based on R1 or clear later rounds
        this.checkIfBracketIsComplete();
      } catch (err) {
        this.error = 'Failed to load bracket structure.';
        console.error(err);
      } finally {
        this.isLoading = false;
      }
    },

    async fetchLeaderboard() {
      this.isLoadingLeaderboard = true;
      try {
        const response = await apiService.getLeaderboard();
        this.leaderboard = response.data;
      } catch (error) {
        console.error("Failed to fetch leaderboard:", error);
        // Handle error display
      } finally {
        this.isLoadingLeaderboard = false;
      }
    },
    
    async fetchSubmissionDetails(submissionId: number | string) {
      this.isLoadingViewedBracket = true;
      this.viewedBracket = null; // Clear previous
      // this.error = null; // Or use a specific error state for this action
      try {
        const response = await apiService.getSubmissionDetails(submissionId);
        this.viewedBracket = response.data;
      } catch (err) {
        console.error(`Failed to fetch submission details for ID ${submissionId}:`, err);
        // this.error = `Failed to load bracket (ID: ${submissionId}).`;
        // Or set a specific error for this view
      } finally {
        this.isLoadingViewedBracket = false;
      }
    },

    async fetchOfficialResults(forceFetch: boolean = false) {
      // Optional: Add logic to avoid fetching too frequently
      // const now = Date.now();
      // if (!forceFetch && this.lastResultsFetchTimestamp && (now - this.lastResultsFetchTimestamp < 60000)) { // e.g., 1 minute cooldown
      //     console.log("Skipping official results fetch; recently updated.");
      //     return;
      // }

      this.isLoadingResults = true;
      // this.error = null; // Keep general error for structure loading separate or combine
      try {
          const response = await apiService.getOfficialResults();
          const officialResultsData = response.data;

          if (this.allSeries.length === 0) {
              // If bracket structure hasn't been loaded yet, this is problematic.
              // For now, we assume fetchBracketStructure has run or will run.
              // Or, this function could populate allSeries if it's empty.
              // Let's merge into existing allSeries.
              console.warn("Fetching official results, but allSeries is empty. Ensure bracket structure is loaded first or simultaneously.");
          }

          // Merge official results into the existing allSeries state
          officialResultsData.forEach(officialSeries => {
              const existingSeries = this.allSeries.find(s => s.id === officialSeries.id);
              if (existingSeries) {
                  existingSeries.status = officialSeries.status;
                  existingSeries.games_team1_won = officialSeries.games_team1_won;
                  existingSeries.games_team2_won = officialSeries.games_team2_won;
                  existingSeries.actual_winner_team_id = officialSeries.actual_winner_team_id;

                  // If series is completed, and teams for next round were TBD,
                  // this is where you might trigger an update to those TBD teams in allSeries
                  // This can get complex and might be better handled by re-evaluating propagation
                  // or having `updateAdvancingTeams` re-run.
                  // For now, this just updates the current series' official data.
              } else {
                  // This case should ideally not happen if allSeries is populated from a similar source.
                  // If it does, you might need to add the series or handle it.
                  console.warn(`Official result for series ID ${officialSeries.id} (${officialSeries.series_identifier}) not found in local allSeries state.`);
              }
          });
          // this.lastResultsFetchTimestamp = Date.now();
          console.log("Official results merged into bracket state.");
      } catch (err) {
          console.error("Error fetching official results:", err);
          // this.error = "Failed to fetch official results."; // Or a specific error state
      } finally {
          this.isLoadingResults = false;
      }
  },

    makePick(seriesId: number, predictedWinnerTeamId: number | null) {
      const series = this.allSeries.find(s => s.id === seriesId);
      if (!series || series.status !== 'PENDING') return;

      if (series.round_number > 1 && !this.canAdvanceToRound(series.round_number)) {
          // Check if the specific series being picked actually has its teams populated
          if (!series.team1_id || !series.team2_id) {
            alert(`Teams for this series are not yet determined. Please complete selections for Round ${series.round_number - 1} first.`);
            return;
          }
      }

      this.userPicks.set(seriesId, predictedWinnerTeamId);
      series.predicted_winner_team_id = predictedWinnerTeamId;
      
      // When a pick is changed, we need to recursively clear subsequent dependent picks
      this.clearSubsequentPicks(series.series_identifier, series.round_number);
      this.updateAdvancingTeams();
      this.checkIfBracketIsComplete();
    },
    
    clearSubsequentPicks(changedSeriesIdentifier: string, changedSeriesRound: number) {
        let seriesToClearQueue = [changedSeriesIdentifier];
        const visitedToClear = new Set<string>();

        while(seriesToClearQueue.length > 0) {
            const currentSourceSeriesId = seriesToClearQueue.shift()!;
            if(visitedToClear.has(currentSourceSeriesId)) continue;
            visitedToClear.add(currentSourceSeriesId);

            const progression = progressionMap[currentSourceSeriesId];
            if (progression) {
                const nextSeriesInLine = this.allSeries.find(s => s.series_identifier === progression.nextSeriesId);
                if (nextSeriesInLine) {
                    // If this next series had a pick, clear it because its input changed
                    if (this.userPicks.get(nextSeriesInLine.id) !== null) {
                        this.userPicks.set(nextSeriesInLine.id, null);
                        nextSeriesInLine.predicted_winner_team_id = null;
                    }
                    // Add this next series to the queue to clear its dependents
                    seriesToClearQueue.push(nextSeriesInLine.series_identifier);
                }
            }
        }
    },


    // _getTeamDetails now needs to return AdvancingTeamDetails
    _getTeamDetails(teamId: number | null): AdvancingTeamDetails {
        if (teamId === null) return { id: null, name: 'TBD', abbr: 'TBD', logo: null };

        // Prioritize finding the team in the original data (most likely R1 teams)
        for (const s of this.originalSeriesData) {
            if (s.team1_id === teamId) return { id: s.team1_id, name: s.team1_name, abbr: s.team1_abbr, logo: s.team1_logo };
            if (s.team2_id === teamId) return { id: s.team2_id, name: s.team2_name, abbr: s.team2_abbr, logo: s.team2_logo };
        }
        // Fallback: if it's an advanced team, its details *should* have been propagated to allSeries
        // This is a bit circular if allSeries isn't fully updated yet, but serves as a lookup if details were set.
        for (const s of this.allSeries) {
           if (s.team1_id === teamId) return { id: s.team1_id, name: s.team1_name, abbr: s.team1_abbr, logo: s.team1_logo };
           if (s.team2_id === teamId) return { id: s.team2_id, name: s.team2_name, abbr: s.team2_abbr, logo: s.team2_logo };
        }
        // Absolute fallback - means team details weren't found/propagated correctly
        console.warn(`_getTeamDetails: Could not find details for teamId ${teamId}. Returning placeholder.`);
        return { id: teamId, name: 'Team ?', abbr: '???', logo: null };
    },

    updateAdvancingTeams() {
      const newAllSeries = JSON.parse(JSON.stringify(this.allSeries)) as Series[];

      // Reset teams for rounds > 1 to their original state or TBD
      newAllSeries.forEach(series => {
        if (series.round_number > 1) {
          const original = this.originalSeriesData.find(os => os.id === series.id);
          series.team1_id = original?.team1_id || null;
          series.team1_name = original?.team1_name || 'TBD';
          series.team1_abbr = original?.team1_abbr || 'TBD';
          series.team1_logo = original?.team1_logo || null;
          series.team2_id = original?.team2_id || null;
          series.team2_name = original?.team2_name || 'TBD';
          series.team2_abbr = original?.team2_abbr || 'TBD';
          series.team2_logo = original?.team2_logo || null;
        }
      });

      // Propagate winners round by round
      for (let r = 1; r < 4; r++) { // Iterate through rounds that *feed* into next rounds
        const seriesInCurrentFeedingRound = newAllSeries.filter(s => s.round_number === r);
        for (const feedingSeries of seriesInCurrentFeedingRound) {
          const winnerId = this.userPicks.get(feedingSeries.id);
          if (winnerId) { // If a winner is picked for this feeding series
            const progressionRule = progressionMap[feedingSeries.series_identifier];
            if (progressionRule) {
              const targetSeries = newAllSeries.find(s => s.series_identifier === progressionRule.nextSeriesId);
              if (targetSeries) {
                const winnerDetails = this._getTeamDetails(winnerId); // Get details of the winner
                if (progressionRule.slot === 'team1') {
                  targetSeries.team1_id = winnerDetails.id;
                  targetSeries.team1_name = winnerDetails.name;
                  targetSeries.team1_abbr = winnerDetails.abbr;
                  targetSeries.team1_logo = winnerDetails.logo;
                } else { // slot === 'team2'
                  targetSeries.team2_id = winnerDetails.id;
                  targetSeries.team2_name = winnerDetails.name;
                  targetSeries.team2_abbr = winnerDetails.abbr;
                  targetSeries.team2_logo = winnerDetails.logo;
                }
              }
            }
          }
        }
      }
      this.allSeries = newAllSeries; // Update the reactive state
    },
    
    checkIfBracketIsComplete() {
        if (this.originalSeriesData.length === 0) {
            this.isBracketCompletelyPicked = false;
            return;
        }
        // A bracket is complete if all 15 series have a non-null pick
        const numPicksMade = Array.from(this.userPicks.values()).filter(pick => pick !== null).length;
        this.isBracketCompletelyPicked = numPicksMade === this.originalSeriesData.length;
    },

    setPlayerName(name: string) {
      this.playerName = name;
    },

    async submitBracket() {
      this.checkIfBracketIsComplete(); // Ensure status is up-to-date
      if (!this.isBracketCompletelyPicked) {
        alert('Please complete all picks in the bracket.');
        return;
      }
      if (!this.playerName.trim()) {
        alert('Please enter your name.');
        return;
      }

      // Use PickPayload for the items in the picks array
      const picksToSubmit: PickPayload[] = [];
      this.userPicks.forEach((winnerId, seriesId) => {
        if (winnerId !== null) {
          picksToSubmit.push({ series_id: seriesId, predicted_winner_team_id: winnerId });
        }
      });

      // Use BracketSubmissionApiPayload for the overall payload
      const payloadForApi: BracketSubmissionApiPayload = {
        player_name: this.playerName,
        picks: picksToSubmit,
      };

      this.isLoading = true;
      this.error = null;
      try {
        const response = await apiService.submitBracket(payloadForApi); // This should now match
        console.log("Bracket submitted successfully:", response.data);
        this.successMessage = `Bracket submitted successfully! Submission ID: ${response.data.submission_id}`; // Set success message
        this.error = null; // Clear any previous errors
        // TODO: Optionally, reset state, clear picks, or navigate to a confirmation page
        this.userPicks.clear();
        this.allSeries.forEach(s => s.predicted_winner_team_id = null);
        this.updateAdvancingTeams(); // Reset visual bracket
        this.playerName = '';
        this.checkIfBracketIsComplete();
    } catch (err: any) {
        this.successMessage = null; // Clear success message
        if (err.response && err.response.data && err.response.data.error) {
            this.error = `Submission Error: ${err.response.data.error}`;
        } else {
            this.error = 'Failed to submit bracket. An unknown error occurred.';
        }
        console.error(err);
    } finally {
        this.isLoading = false;
      }
    },
  },
});