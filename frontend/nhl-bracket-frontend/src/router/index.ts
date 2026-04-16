// frontend/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import LandingView from '../views/LandingView.vue';
import PlayoffBracket from '../components/PlayoffBracket.vue'; // Or wherever your main bracket view is
import LeaderboardView from '../views/LeaderboardView.vue'; // Assuming you created this
import AdminView from '../views/AdminView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/welcome',
      name: 'Landing',
      component: LandingView
    },
    {
      path: '/admin',
      name: 'Admin',
      component: AdminView,
      // Optional: Add a meta check if you want to protect it
      meta: { requiresAccess: true } 
    },
    {
      path: '/',
      name: 'Bracket', // Or 'Home'
      component: () => import('../components/PlayoffBracket.vue'),
      meta: { requiresAuth: true } // Mark as protected
    },
    {
      path: '/leaderboard', // The path for your leaderboard
      name: 'Leaderboard',
      component: () => import('../views/LeaderboardView.vue'),
      meta: { requiresAuth: true } // Mark as protected
    },
    // ... your other routes (like viewing a specific bracket, about page, etc.)
    {
      path: '/bracket/:submissionId', // Example for viewing a specific submission
      name: 'ViewBracket',
      component: () => import('../views/ViewBracketView.vue'), // Lazy load
      meta: { requiresAuth: true }, // Mark as protected
      props: true // Passes route params as props
    }
  ]
});

// THE BOUNCER LOGIC
router.beforeEach((to, from, next) => {
  const isAuthorized = localStorage.getItem('lola_access_granted') === 'true';

  if (to.meta.requiresAuth && !isAuthorized) {
    // If trying to access a protected page without the code
    next({ name: 'Landing' });
  } else if (to.name === 'Landing' && isAuthorized) {
    // If already authorized, don't show landing page again
    next({ name: 'Bracket' });
  } else {
    next();
  }
});

export default router;