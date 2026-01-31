<template>
  <div class="container">
    <div class="brand">
      <div class="brand-dot"></div>
      <div>
        <h1>flickfeast</h1>
        <p>Pick a movie, cook the mood.</p>
      </div>
    </div>

    <div v-if="!user" class="panel">
      <strong>Sign in to continue</strong>
      <div id="google-signin"></div>
      <p v-if="missingClientId" class="note">
        Missing VITE_GOOGLE_CLIENT_ID. Add it to frontend/.env and restart Vite.
      </p>
      <p class="note">
        Use your Google account to unlock personalized movie pairing ideas.
      </p>
    </div>

    <div v-else class="panel">
      <div class="user-card">
        <img :src="user.picture" alt="User avatar" />
        <div>
          <strong>Welcome, {{ user.name }}</strong>
          <p>{{ user.email }}</p>
        </div>
      </div>

      <label for="movie">What movie are we watching?</label>
      <input
        id="movie"
        v-model="movieTitle"
        type="text"
        placeholder="Type a movie title"
        @keyup.enter="submitMovie"
      />
      <button @click="submitMovie">Continue</button>
      <p v-if="movieResponse" class="note">{{ movieResponse }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";

const user = ref(null);
const movieTitle = ref("");
const movieResponse = ref("");
const missingClientId = ref(false);

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

async function handleCredentialResponse(response) {
  try {
    const res = await fetch(`${apiBaseUrl}/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_token: response.credential }),
    });

    if (!res.ok) {
      throw new Error("Authentication failed");
    }

    user.value = await res.json();
  } catch (err) {
    console.error(err);
    alert("Google sign-in failed. Check backend logs and client ID.");
  }
}

async function submitMovie() {
  const title = movieTitle.value.trim();
  if (!title) {
    movieResponse.value = "Please enter a movie title.";
    return;
  }

  const res = await fetch(`${apiBaseUrl}/movies/lookup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });

  if (!res.ok) {
    movieResponse.value = "Unable to save movie right now.";
    return;
  }

  const data = await res.json();
  movieResponse.value = data.message;
}

onMounted(() => {
  if (!googleClientId) {
    console.warn("Missing VITE_GOOGLE_CLIENT_ID");
    missingClientId.value = true;
    return;
  }

  const initGoogle = () => {
    if (!window.google || !window.google.accounts) {
      setTimeout(initGoogle, 200);
      return;
    }

    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: handleCredentialResponse,
    });

    window.google.accounts.id.renderButton(
      document.getElementById("google-signin"),
      { theme: "outline", size: "large", width: 280 }
    );
  };

  initGoogle();
});
</script>
