// frontend/src/services/apiService.ts

import axios, { type AxiosResponse } from 'axios';
import type {
    Player,
    Team,
    Series,
    BracketSubmissionApiPayload,
    BracketSubmissionApiResponse,
    LeaderboardEntry,
    DetailedBracketView
} from '@/types';

// Define type for playoff status response
export interface PlayoffStatusResponse {
    playoffs_started: boolean;
}

// 1. Debug log to see exactly what Vite "baked" into the code
console.log('--- DEBUG: VITE_API_BASE_URL is:', import.meta.env.VITE_API_BASE_URL);

// 2. Fallback logic: Ensure it always has https:// and points to your production backend
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://nhl-bracket-2026-production.up.railway.app/api';

const apiClient = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export default {
    // NEW: The Access Code verification method
    verifyAccess(code: string): Promise<AxiosResponse<{ success: boolean; message: string }>> {
        return apiClient.post('/verify_access', { code });
    },

    getPlayers(): Promise<AxiosResponse<Player[]>> {
        return apiClient.get('/players');
    },

    addPlayer(name: string): Promise<AxiosResponse<{ message: string; player: Player }>> {
        return apiClient.post('/players', { name });
    },

    getTeams(): Promise<AxiosResponse<Team[]>> {
        return apiClient.get('/teams');
    },

    getPlayoffBracketStructure(): Promise<AxiosResponse<Series[]>> {
        return apiClient.get('/playoff_bracket_structure');
    },

    submitBracket(submissionPayload: BracketSubmissionApiPayload): Promise<AxiosResponse<BracketSubmissionApiResponse>> {
        return apiClient.post('/bracket_submissions', submissionPayload);
    },

    getOfficialResults(): Promise<AxiosResponse<Series[]>> {
        return apiClient.get('/official_results');
    },

    getLeaderboard(): Promise<AxiosResponse<LeaderboardEntry[]>> {
        return apiClient.get('/leaderboard');
    },

    getPlayoffStatus(): Promise<AxiosResponse<PlayoffStatusResponse>> {
        return apiClient.get('/playoff_status');
    },

    getSubmissionDetails(submissionId: number | string): Promise<AxiosResponse<DetailedBracketView>> {
        return apiClient.get(`/bracket_submissions/${submissionId}`);
    }
};