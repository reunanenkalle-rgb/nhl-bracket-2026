// frontend/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import PlayoffBracket from '../components/PlayoffBracket.vue'; // Or wherever your main bracket view is
import LeaderboardView from '../views/LeaderboardView.vue'; // Assuming you created this

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Bracket', // Or 'Home'
      component: PlayoffBracket 
    },
    {
      path: '/leaderboard', // The path for your leaderboard
      name: 'Leaderboard',
      component: LeaderboardView 
    },
    // ... your other routes (like viewing a specific bracket, about page, etc.)
    {
      path: '/bracket/:submissionId', // Example for viewing a specific submission
      name: 'ViewBracket',
      component: () => import('../views/ViewBracketView.vue'), // Lazy load
      props: true // Passes route params as props
    }
  ]
});

export default router;