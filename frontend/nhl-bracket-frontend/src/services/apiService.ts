import axios, { type AxiosResponse } from 'axios';
import type { Player, Team, BracketSubmission } from '@/types'; // Adjust path

const apiClient = axios.create({
    baseURL: 'http://localhost:5000/api',
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
        return apiClient.get('/teams');
    },
    submitBracket(submissionData: Omit<BracketSubmission, 'id' | 'player_id'>, playerId: number): Promise<AxiosResponse<{ message: string; submission: BracketSubmission }>> {
        // The actual payload structure will depend on your backend endpoint
        const payload = {
            ...submissionData,
            player_id: playerId,
        };
        return apiClient.post('/bracket_submissions', payload);
    }
    // Add more functions here
};