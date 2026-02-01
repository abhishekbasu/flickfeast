<template>
  <div class="app-shell" :class="{ 'search-bg': !showSplash }">
    <div v-if="showSplash" class="splash">
      <div class="splash-card">
        <img
          class="splash-image"
          src="/flickfeast.png"
          alt="flickfeast splash"
        />
        <div class="splash-actions">
          <h2>Movie-inspired recipes & party ideas</h2>
          <p>Pick a film and let the party menu come to life.</p>
          <button v-if="!isTestMode" type="button" @click="startGoogleLogin">
            Continue with Google
          </button>
          <button v-else type="button" @click="bypassLogin">
            Continue in test mode
          </button>
          <p v-if="missingClientId" class="note">
            Missing VITE_GOOGLE_CLIENT_ID. Add it to frontend/.env and restart Vite.
          </p>
          <button type="button" :disabled="!canStart" @click="showSplash = false">
            Start planning
          </button>
          <p v-if="!user" class="note">
            Please sign in to continue.
          </p>
        </div>
      </div>
    </div>

    <div v-else class="container">
    <div class="brand">
      <div class="brand-dot"></div>
      <div>
        <h1>flickfeast</h1>
        <p>Pick a movie, cook the mood.</p>
      </div>
    </div>

    <div v-if="!user" class="panel">
      <strong>Sign in to continue</strong>
      <button v-if="!isTestMode" type="button" @click="startGoogleLogin">
        Continue with Google
      </button>
      <button v-else-if="!user" type="button" @click="bypassLogin">
        Continue in test mode
      </button>
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

      <div class="panel-grid" :class="{ selected: selectedMovie }">
        <div v-if="selectedMovie" class="selected-movie">
          <img :src="selectedMovie.poster" alt="" />
          <div>
            <div class="selected-title">{{ selectedMovie.title }}</div>
            <div class="selected-year">{{ selectedMovie.year }}</div>
          </div>
        </div>

        <div class="panel-main">
          <template v-if="!isSubmitting">
            <label for="movie">What movie are we watching?</label>
            <input
              id="movie"
              v-model="movieTitle"
              type="text"
              placeholder="Type a movie title"
              :disabled="selectedMovie || isSubmitting"
              @input="queueSearch"
              @keyup.enter="submitMovie"
            />
            <button :disabled="isSubmitting || selectedMovie" @click="submitMovie">
              Continue
            </button>
            <button
              v-if="selectedMovie"
              type="button"
              class="secondary-button"
              @click="clearSelection"
            >
              Search another movie
            </button>
          </template>
          <div v-else class="loading">
            <div class="loading-text">Generating your dream menu</div>
            <div class="loading-bar">
              <span></span>
            </div>
          </div>
          <div v-if="searchResults.length" class="results">
            <div class="note">Select the best match:</div>
            <button
              v-for="result in searchResults"
              :key="result.title + result.year + result.imdb_id"
              type="button"
              class="result-item"
              @click="selectMovie(result)"
            >
              <img
                v-if="result.poster"
                :src="result.poster"
                alt=""
                class="result-poster"
              />
              <div v-else class="result-poster placeholder">No image</div>
              <div class="result-info">
                <div class="result-title">{{ result.title }}</div>
                <div class="result-meta">{{ result.year }}</div>
              </div>
            </button>
          </div>
          <div v-else-if="showEmptyState" class="empty-state">
            <img
              class="empty-illustration"
              src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='120' viewBox='0 0 140 120'><rect width='140' height='120' rx='24' fill='%23f6f3ff'/><circle cx='50' cy='52' r='18' fill='%23d8cffb'/><rect x='28' y='74' width='88' height='22' rx='11' fill='%23d8cffb'/><path d='M83 40c9 1 16 9 16 18' stroke='%23958ad6' stroke-width='4' stroke-linecap='round' fill='none'/></svg>"
              alt=""
            />
            <div>
              <div class="empty-title">Oops, we didn’t find that one.</div>
              <div class="empty-text">Try a different title or check the spelling.</div>
            </div>
          </div>
        </div>
      </div>
      <p v-if="movieResponse" class="note">{{ movieResponse }}</p>
      <div v-if="menuItems.length" class="menu-grid">
        <div
          v-for="item in menuItems"
          :key="item.name"
          class="menu-card"
          @click="openRecipe(item)"
        >
          <img v-if="item.image_data" :src="item.image_data" alt="" />
          <div class="menu-title">{{ item.name }}</div>
          <div class="menu-reason">{{ item.reason }}</div>
        </div>
      </div>
      <p v-if="menuNotes" class="note">{{ menuNotes }}</p>
    </div>
    </div>
  </div>

  <div v-if="activeRecipe" class="modal-backdrop" @click="closeRecipe">
    <div class="modal" @click.stop>
      <div class="modal-header">
        <div>
          <div class="modal-title">{{ activeRecipe.name }}</div>
          <div class="modal-subtitle">{{ activeRecipe.recipe.title }}</div>
        </div>
        <button type="button" class="modal-close" @click="closeRecipe">Close</button>
      </div>
      <a
        v-if="activeRecipe.recipe.url"
        class="modal-link"
        :href="activeRecipe.recipe.url"
        target="_blank"
        rel="noreferrer"
      >
        {{ activeRecipe.recipe.source || "Recipe source" }}
      </a>
      <div v-if="activeRecipe.recipe.ingredients?.length" class="recipe-section">
        <div class="recipe-label">Ingredients</div>
        <ul>
          <li v-for="line in activeRecipe.recipe.ingredients" :key="line">{{ line }}</li>
        </ul>
      </div>
      <div v-if="activeRecipe.recipe.steps?.length" class="recipe-section">
        <div class="recipe-label">Steps</div>
        <ol>
          <li v-for="step in activeRecipe.recipe.steps" :key="step">{{ step }}</li>
        </ol>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

const user = ref(null);
const movieTitle = ref("");
const movieResponse = ref("");
const menuItems = ref([]);
const menuNotes = ref("");
const activeRecipe = ref(null);
const searchResults = ref([]);
const showEmptyState = ref(false);
const selectedMovie = ref(null);
const isSubmitting = ref(false);
let searchTimeout = null;
const missingClientId = ref(false);
const showSplash = ref(true);
const canStart = computed(() => Boolean(user.value));
const isTestMode =
  import.meta.env.VITE_IN_TEST === "true" ||
  import.meta.env.IN_TEST === "true";

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
    showSplash.value = false;
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

  isSubmitting.value = true;
  const res = await fetch(`${apiBaseUrl}/movies/menu`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });

  if (!res.ok) {
    movieResponse.value = "Unable to build a menu right now.";
    menuItems.value = [];
    menuNotes.value = "";
    activeRecipe.value = null;
    isSubmitting.value = false;
    return;
  }

  const data = await res.json();
  menuItems.value = data.items || [];
  const notes = data.notes || "";
  menuNotes.value = notes.toLowerCase().includes("no recipes") ? "" : notes;
  activeRecipe.value = null;
  movieResponse.value = menuItems.value.length
    ? "Here is your movie-themed menu."
    : "No menu items found.";
  searchResults.value = [];
  isSubmitting.value = false;
}

onMounted(() => {
  const cachedUser = localStorage.getItem("ff_user");
  if (cachedUser) {
    try {
      user.value = JSON.parse(cachedUser);
    } catch (err) {
      localStorage.removeItem("ff_user");
    }
  }
  if (isTestMode) {
    return;
  }
  if (!googleClientId) {
    console.warn("Missing VITE_GOOGLE_CLIENT_ID");
    missingClientId.value = true;
    return;
  }

  if (!googleClientId) {
    console.warn("Missing VITE_GOOGLE_CLIENT_ID");
    missingClientId.value = true;
  }
});

function bypassLogin() {
  user.value = {
    name: "Test User",
    email: "test@example.com",
    picture:
      "data:image/svg+xml;utf8," +
      "<svg xmlns='http://www.w3.org/2000/svg' width='96' height='96' viewBox='0 0 96 96'>" +
      "<rect width='96' height='96' rx='24' fill='%23f1f3ff'/>" +
      "<circle cx='48' cy='38' r='16' fill='%23c7cbe8'/>" +
      "<rect x='22' y='58' width='52' height='24' rx='12' fill='%23c7cbe8'/>" +
      "</svg>",
  };
}

function queueSearch() {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  searchTimeout = setTimeout(runSearch, 500);
}

async function runSearch() {
  const query = movieTitle.value.trim();
  if (query.length < 2) {
    searchResults.value = [];
    showEmptyState.value = false;
    return;
  }
  const res = await fetch(`${apiBaseUrl}/movies/search?query=${encodeURIComponent(query)}`);
  if (!res.ok) {
    searchResults.value = [];
    showEmptyState.value = true;
    return;
  }
  const data = await res.json();
  searchResults.value = data.filter((result) => result.poster);
  showEmptyState.value = searchResults.value.length === 0;
}

function selectMovie(result) {
  movieTitle.value = result.title;
  searchResults.value = [];
  showEmptyState.value = false;
  selectedMovie.value = result;
  submitMovie();
}

function clearSelection() {
  selectedMovie.value = null;
  menuItems.value = [];
  menuNotes.value = "";
  movieResponse.value = "";
}

function openRecipe(item) {
  if (!item.recipe) {
    return;
  }
  activeRecipe.value = { name: item.name, recipe: item.recipe };
}

function closeRecipe() {
  activeRecipe.value = null;
}

async function startGoogleLogin() {
  try {
    const res = await fetch(`${apiBaseUrl}/auth/google/start`);
    if (!res.ok) {
      throw new Error("Failed to start auth");
    }
    const data = await res.json();
    window.location.href = data.auth_url;
  } catch (err) {
    console.error(err);
    alert("Unable to start Google sign-in.");
  }
}
</script>
