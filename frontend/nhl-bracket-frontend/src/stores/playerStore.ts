import { defineStore } from 'pinia';
import type { Player } from '@/types';
import apiService from '@/services/apiService';

interface PlayerState {
  players: Player[];
  currentPlayer: Player | null;
  isLoading: boolean;
  error: string | null;
}

export const usePlayerStore = defineStore('player', {
  state: (): PlayerState => ({
    players: [],
    currentPlayer: null,
    isLoading: false,
    error: null,
  }),
  actions: {
    async fetchPlayers() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await apiService.getPlayers();
        this.players = response.data;
      } catch (err) {
        this.error = 'Failed to fetch players';
        console.error(err);
      } finally {
        this.isLoading = false;
      }
    },
    // ... other actions like addPlayer, setCurrentPlayer
  },
});