// frontend/src/services/apiService.ts

import axios, { type AxiosResponse } from 'axios';
import type {
    Player,
    Team,
    Series,
    BracketSubmissionApiPayload, // Use the new payload type
    BracketSubmissionApiResponse // Use the new response type
} from '@/types'; // Ensure this path is correct

const apiClient = axios.create({
    baseURL: 'http://localhost:5000/api', // Your Flask backend URL
    headers: {
        'Content-Type': 'application/json',
    },
});

export default {
    getPlayers(): Promise<AxiosResponse<Player[]>> {
        return apiClient.get('/players');
    },

    addPlayer(name: string): Promise<AxiosResponse<{ message: string; player: Player }>> {
        return apiClient.post('/players', { name });
    },

    getTeams(): Promise<AxiosResponse<Team[]>> {
        // Ensure your backend /api/teams returns data matching the Team interface
        return apiClient.get('/teams');
    },

    getPlayoffBracketStructure(): Promise<AxiosResponse<Series[]>> {
        return apiClient.get('/playoff_bracket_structure');
    },

    /**
     * Submits the completed bracket to the backend.
     * @param submissionPayload - The data for the bracket submission.
     * Should conform to BracketSubmissionApiPayload interface.
     */
    submitBracket(submissionPayload: BracketSubmissionApiPayload): Promise<AxiosResponse<BracketSubmissionApiResponse>> {
        // The submissionPayload already contains player_name and picks array
        // as expected by the backend endpoint designed earlier.
        return apiClient.post('/bracket_submissions', submissionPayload);
    },

    getOfficialResults(): Promise<AxiosResponse<Series[]>> {
        return apiClient.get('/official_results');
    }

    // You can add more functions here as your app grows, for example:
    // getSubmittedBracket(submissionId: number): Promise<AxiosResponse<FullBracketDetails>> {
    //   return apiClient.get(`/bracket_submissions/${submissionId}`);
    // },
    // getLeaderboard(): Promise<AxiosResponse<LeaderboardEntry[]>> {
    //   return apiClient.get('/leaderboard');
    // }
};