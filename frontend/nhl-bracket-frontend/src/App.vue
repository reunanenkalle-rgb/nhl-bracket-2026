<template>
  <div id="app-container"> <header>
      <h1>LoLa Viralline NHL Playoff Bracket Challenge</h1>
      </header>
    <main>
      <RouterView /> </main>
  </div>
</template>

<script lang="ts" setup>
import { RouterView, RouterLink } from 'vue-router'; // RouterLink is optional for now
</script>

<style>
/* Your global styles or styles for App.vue */
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: #f0f2f5; /* A slightly different background */
  color: #333;
}

#app-container { /* Changed from #app to avoid potential conflicts */
  max-width: 1400px; /* Max width for the overall app container */
  margin: 0 auto; /* Center the container */
  padding: 15px; /* Padding around the container */
}

header {
  background-color: #003366; /* Dark blue for header */
  padding: 15px 20px;
  border-radius: 8px 8px 0 0; /* Rounded top corners */
  margin-bottom: 15px; /* Space below header */
}

header h1 {
  text-align: center;
  color: #ffffff; /* White text */
  margin: 0;
  font-size: 1.8em;
}

/* Optional: Styles for navigation if you add RouterLinks */
/*
nav {
  text-align: center;
  margin-top: 10px;
}
nav a {
  color: #f0f2f5;
  margin: 0 10px;
  text-decoration: none;
  font-weight: 500;
}
nav a.router-link-exact-active {
  color: #ffc107;
  border-bottom: 2px solid #ffc107;
}
*/

main {
  background-color: #ffffff; /* White background for main content area */
  padding: 20px;
  border-radius: 0 0 8px 8px; /* Rounded bottom corners if header is separate */
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08); /* Softer shadow */
}
</style>