<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, PointElement, LineElement, CategoryScale, LinearScale } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, PointElement, LineElement, CategoryScale, LinearScale)

const gameId = ref<any>(null)
const searchQuery = ref('')
const isSearching = ref(false)
const searchResults = ref<any[]>([])
let searchTimeout: any = null

const gamesList = ref<any[]>([])
const featuredGames = ref<any[]>([])
const region1 = ref('pl')
const region2 = ref('de')
const wageType = ref('min')
const wage1 = ref(0)
const wage2 = ref(0)
const wagesData = ref<Record<string, any>>({})
const isLoading = ref(false)
const resultData = ref<any>(null)
const historyData = ref<any>(null)
const basketData = ref<any>(null)

let rotationInterval: any = null

const availableRegions = [
  { title: 'Polska (PLN)', value: 'pl' },
  { title: 'USA (USD)', value: 'us' },
  { title: 'Wielka Brytania (GBP)', value: 'gb' },
  { title: 'Niemcy (EUR)', value: 'de' },
  { title: 'Francja (EUR)', value: 'fr' },
  { title: 'Australia (AUD)', value: 'au' },
  { title: 'Belgia (EUR)', value: 'be' },
  { title: 'Brazylia (BRL)', value: 'br' },
  { title: 'Kanada (CAD)', value: 'ca' },
  { title: 'Szwajcaria (CHF)', value: 'ch' },
  { title: 'Dania (DKK)', value: 'dk' },
  { title: 'Hiszpania (EUR)', value: 'es' },
  { title: 'Unia Europejska (EUR)', value: 'eu' },
  { title: 'Finlandia (EUR)', value: 'fi' },
  { title: 'Irlandia (EUR)', value: 'ie' },
  { title: 'Włochy (EUR)', value: 'it' },
  { title: 'Holandia (EUR)', value: 'nl' },
  { title: 'Norwegia (NOK)', value: 'no' },
  { title: 'Szwecja (SEK)', value: 'se' }
]

const displayedGames = computed(() => {
  return searchQuery.value && searchResults.value.length > 0 ? searchResults.value : gamesList.value
})

const getImageUrl = (appId: string | number) => {
  return `https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/${appId}/header.jpg`
}

const updateWages = () => {
  if (wagesData.value[region1.value]) {
    wage1.value = wagesData.value[region1.value][wageType.value]
  }
  if (wagesData.value[region2.value]) {
    wage2.value = wagesData.value[region2.value][wageType.value]
  }
}

watch([region1, region2, wageType], updateWages)

watch(searchQuery, (val) => {
  if (typeof val !== 'string' || !val || val.length < 3) {
    searchResults.value = []
    return
  }
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(async () => {
    isSearching.value = true
    try {
      const response = await axios.get(`http://127.0.0.1:8000/api/search?query=${val}`)
      searchResults.value = response.data.games
    } catch (error) {
    } finally {
      isSearching.value = false
    }
  }, 500)
})

const rotateFeaturedGames = () => {
  if (gamesList.value.length === 0) return
  const shuffled = [...gamesList.value].sort(() => 0.5 - Math.random())
  featuredGames.value = shuffled.slice(0, 8)
}

const selectFeatured = (appId: string) => {
  const game = gamesList.value.find(g => g.value === appId)
  if (game) {
    gameId.value = game
    compareData()
  }
}

const fetchInitialData = async () => {
  try {
    const [wagesRes, gamesRes] = await Promise.all([
      axios.get('http://127.0.0.1:8000/api/wages'),
      axios.get('http://127.0.0.1:8000/api/top-games')
    ])
    wagesData.value = wagesRes.data
    gamesList.value = gamesRes.data.games.map((g: any) => ({
      title: g.name,
      value: g.appid
    }))
    updateWages()
    rotateFeaturedGames()
    rotationInterval = setInterval(rotateFeaturedGames, 5000)
  } catch (error) {
  }
}

const compareData = async () => {
  if (!gameId.value) return
  isLoading.value = true

  const actualAppId = typeof gameId.value === 'object' ? gameId.value.value : gameId.value

  try {
    const [compRes, histRes, basketRes] = await Promise.all([
      axios.get('http://127.0.0.1:8000/api/compare', {
        params: { app_id: actualAppId, region1: region1.value, region2: region2.value, wage1: wage1.value, wage2: wage2.value }
      }),
      axios.get('http://127.0.0.1:8000/api/dw/history', {
        params: { region1: region1.value, region2: region2.value }
      }),
      axios.get('http://127.0.0.1:8000/api/dw/basket', {
        params: { region1: region1.value, region2: region2.value, wage1: wage1.value, wage2: wage2.value }
      })
    ])

    const workHoursPerMonth = 168
    const hourly1 = wage1.value / workHoursPerMonth
    const hourly2 = wage2.value / workHoursPerMonth

    const copies1 = compRes.data.region1_copies
    const copies2 = compRes.data.region2_copies

    let multiplierText = ''
    if (copies1 > copies2 && copies2 > 0) {
      multiplierText = `W regionie ${region1.value.toUpperCase()} kupisz ${(copies1 / copies2).toFixed(1)}x więcej kopii niż w ${region2.value.toUpperCase()}`
    } else if (copies2 > copies1 && copies1 > 0) {
      multiplierText = `W regionie ${region2.value.toUpperCase()} kupisz ${(copies2 / copies1).toFixed(1)}x więcej kopii niż w ${region1.value.toUpperCase()}`
    } else {
      multiplierText = `Siła nabywcza w obu regionach jest zbliżona`
    }

    const daily1 = wage1.value / 21
    const daily2 = wage2.value / 21

    resultData.value = {
      ...compRes.data,
      app_id: actualAppId,
      image: getImageUrl(actualAppId),
      pct1: ((compRes.data.region1_price / wage1.value) * 100).toFixed(2),
      pct2: ((compRes.data.region2_price / wage2.value) * 100).toFixed(2),
      hours1: (compRes.data.region1_price / hourly1).toFixed(1),
      hours2: (compRes.data.region2_price / hourly2).toFixed(1),
      daily_copies1: (daily1 / compRes.data.region1_price).toFixed(2),
      daily_copies2: (daily2 / compRes.data.region2_price).toFixed(2),
      multiplierMsg: multiplierText
    }

    basketData.value = basketRes.data

    historyData.value = {
      labels: histRes.data.years,
      datasets: [
        {
          label: region1.value.toUpperCase(),
          borderColor: '#7C4DFF',
          backgroundColor: '#7C4DFF',
          data: histRes.data.region1_data,
          tension: 0.4,
          borderWidth: 3
        },
        {
          label: region2.value.toUpperCase(),
          borderColor: '#00E5FF',
          backgroundColor: '#00E5FF',
          data: histRes.data.region2_data,
          tension: 0.4,
          borderWidth: 3
        }
      ]
    }
  } catch (error) {
  } finally {
    isLoading.value = false
  }
}

const getFullBoxes = (copies: number) => Math.floor(copies)
const getPartialBoxHeight = (copies: number) => `${(copies % 1) * 100}%`

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { labels: { color: 'white' } } },
  scales: {
    y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#ccc' } },
    x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#ccc' } }
  }
}

onMounted(() => {
  fetchInitialData()
})

onUnmounted(() => {
  if (rotationInterval) clearInterval(rotationInterval)
})
</script>

<template>
  <v-app class="app-background">
    <v-main>
      <v-container class="py-10">
        <div class="text-center mb-10">
          <h1 class="text-h2 font-weight-black gradient-text mb-2">Power Purchasing OLAP</h1>
          <p class="text-h6 text-grey-lighten-1">Wielowymiarowa analiza siły nabywczej graczy</p>
        </div>

        <v-row class="mb-8" justify="center">
          <v-col cols="6" sm="4" md="3" v-for="game in featuredGames" :key="game.value">
            <v-card
              class="featured-card rounded-xl overflow-hidden cursor-pointer"
              elevation="12"
              @click="selectFeatured(game.value)"
            >
              <v-img :src="getImageUrl(game.value)" height="120" cover>
                <div class="fill-height d-flex align-end pb-2 px-3 game-title-overlay">
                  <span class="text-subtitle-2 text-white font-weight-bold text-truncate">{{ game.title }}</span>
                </div>
              </v-img>
            </v-card>
          </v-col>
        </v-row>

        <v-card class="pa-8 rounded-xl glass-card mx-auto" max-width="1200" theme="dark">
          <v-autocomplete
            v-model="gameId"
            v-model:search="searchQuery"
            :items="displayedGames"
            item-title="title"
            item-value="value"
            :loading="isSearching"
            label="Wpisz nazwę gry lub wybierz z Top 100"
            variant="outlined"
            color="cyan-accent-3"
            bg-color="rgba(0,0,0,0.4)"
            prepend-inner-icon="mdi-magnify"
            class="mb-6"
            hide-no-data
            return-object
          ></v-autocomplete>

          <div class="d-flex justify-center mb-6">
            <v-btn-toggle v-model="wageType" color="cyan-accent-3" rounded="pill" mandatory group>
              <v-btn value="min" class="px-6">Pensja Minimalna</v-btn>
              <v-btn value="avg" class="px-6">Pensja Średnia</v-btn>
            </v-btn-toggle>
          </div>

          <v-row>
            <v-col cols="12" md="6">
              <v-card variant="outlined" color="deep-purple-accent-1" class="pa-5 rounded-lg bg-black bg-opacity-20">
               <v-select v-model="region1" :items="availableRegions" label="Kraj 1" variant="underlined" color="deep-purple-accent-1">
                  <template v-slot:selection="{ item }">
                    <v-avatar size="24" rounded="sm" class="mr-3">
                      <img :src="`https://flagcdn.com/w40/${item.value}.png`" style="width: 100%; height: 100%; object-fit: cover;">
                    </v-avatar>
                    <span>{{ item.title }}</span>
                  </template>
                  <template v-slot:item="{ props, item }">
                    <v-list-item v-bind="props" :title="item.title">
                      <template v-slot:prepend>
                        <v-avatar size="24" rounded="sm" class="mr-3">
                          <img :src="`https://flagcdn.com/w40/${item.value}.png`" style="width: 100%; height: 100%; object-fit: cover;">
                        </v-avatar>
                      </template>
                    </v-list-item>
                  </template>
                </v-select>
                <v-text-field v-model.number="wage1" label="Zarobki netto" type="number" variant="outlined" color="deep-purple-accent-1" hide-details></v-text-field>
              </v-card>
            </v-col>

            <v-col cols="12" md="6">
              <v-card variant="outlined" color="cyan-accent-3" class="pa-5 rounded-lg bg-black bg-opacity-20">
                <v-select v-model="region2" :items="availableRegions" label="Kraj 2" variant="underlined" color="cyan-accent-3">
                  <template v-slot:selection="{ item }">
                    <v-avatar size="24" rounded="sm" class="mr-3">
                      <img :src="`https://flagcdn.com/w40/${item.value}.png`" style="width: 100%; height: 100%; object-fit: cover;">
                    </v-avatar>
                    <span>{{ item.title }}</span>
                  </template>
                  <template v-slot:item="{ props, item }">
                    <v-list-item v-bind="props" :title="item.title">
                      <template v-slot:prepend>
                        <v-avatar size="24" rounded="sm" class="mr-3">
                          <img :src="`https://flagcdn.com/w40/${item.value}.png`" style="width: 100%; height: 100%; object-fit: cover;">
                        </v-avatar>
                      </template>
                    </v-list-item>
                  </template>
                </v-select>
                <v-text-field v-model.number="wage2" label="Zarobki netto" type="number" variant="outlined" color="cyan-accent-3" hide-details></v-text-field>
              </v-card>
            </v-col>
          </v-row>

          <v-btn block size="x-large" color="cyan-darken-3" class="mt-8 rounded-lg font-weight-bold" elevation="8" @click="compareData" :loading="isLoading" :disabled="!gameId">
            <v-icon left class="mr-2">mdi-database-search</v-icon> Wykonaj Analizę
          </v-btn>
        </v-card>

        <v-expand-transition>
          <div v-if="resultData" class="mt-10">
            <v-card class="pa-8 rounded-xl glass-card mx-auto" max-width="1200" theme="dark">
              <v-row align="center" class="mb-8">
                <v-col cols="12" sm="4">
                  <v-img :src="resultData.image" class="rounded-lg elevation-10" cover aspect-ratio="16/9"></v-img>
                </v-col>
                <v-col cols="12" sm="8">
                  <h2 class="text-h4 font-weight-bold text-cyan-accent-1">{{ resultData.game_title }}</h2>
                  <p class="text-subtitle-1 text-grey-lighten-1 mt-2">Szczegółowy raport siły nabywczej na podstawie wybranego tytułu.</p>
                </v-col>
              </v-row>

              <v-divider class="mb-8"></v-divider>
<v-row class="mt-6">
                <v-col cols="12" md="6">
                  <v-card variant="tonal" color="deep-purple-accent-2" class="pa-4 rounded-lg d-flex align-center">
                    <v-icon size="40" class="mr-4">mdi-clock-outline</v-icon>
                    <div>
                      <div class="text-caption text-uppercase">Czas pracy na 1 kopię</div>
                      <div class="text-h5 font-weight-bold">{{ resultData.hours1 }} <span class="text-body-2">godzin</span></div>
                    </div>
                  </v-card>
                  <v-card variant="tonal" color="deep-purple-lighten-3" class="mt-4 pa-4 rounded-lg d-flex align-center">
                    <v-icon size="40" class="mr-4">mdi-calendar-today</v-icon>
                    <div>
                      <div class="text-caption text-uppercase">Kopie za 1 dzień pracy</div>
                      <div class="text-h5 font-weight-bold">{{ resultData.daily_copies1 }} <span class="text-body-2">szt.</span></div>
                    </div>
                  </v-card>
                </v-col>

                <v-col cols="12" md="6">
                  <v-card variant="tonal" color="cyan-accent-4" class="pa-4 rounded-lg d-flex align-center">
                    <v-icon size="40" class="mr-4">mdi-clock-outline</v-icon>
                    <div>
                      <div class="text-caption text-uppercase">Czas pracy na 1 kopię</div>
                      <div class="text-h5 font-weight-bold">{{ resultData.hours2 }} <span class="text-body-2">godzin</span></div>
                    </div>
                  </v-card>
                  <v-card variant="tonal" color="cyan-lighten-3" class="mt-4 pa-4 rounded-lg d-flex align-center">
                    <v-icon size="40" class="mr-4">mdi-calendar-today</v-icon>
                    <div>
                      <div class="text-caption text-uppercase">Kopie za 1 dzień pracy</div>
                      <div class="text-h5 font-weight-bold">{{ resultData.daily_copies2 }} <span class="text-body-2">szt.</span></div>
                    </div>
                  </v-card>
                </v-col>
              </v-row>

              <v-alert v-if="resultData.multiplierMsg" icon="mdi-trophy" color="amber-darken-3" variant="tonal" class="mb-8 mt-5 rounded-lg" border="start">
                <div class="text-h6 font-weight-bold">{{ resultData.multiplierMsg }}</div>
              </v-alert>

              <v-row>
                <v-col cols="12" md="6">
                  <div class="text-center mb-4 d-flex flex-column align-center">
                    <v-avatar size="48" rounded="sm" class="mb-3 elevation-8" style="border: 1px solid rgba(255,255,255,0.2);">
                      <img :src="`https://flagcdn.com/w80/${region1}.png`" style="width: 100%; height: 100%; object-fit: cover;">
                    </v-avatar>
                    <h3 class="text-h5 font-weight-bold text-deep-purple-accent-1">{{ region1.toUpperCase() }}</h3>
                    <div class="text-h3 font-weight-black mt-2">{{ resultData.region1_copies }} <span class="text-subtitle-1">kopii</span></div>
                    <div class="text-body-2 text-grey">Cena: {{ resultData.region1_price }} {{ resultData.region1_currency }}</div>
                  </div>
                  <div class="waffle-container">
                    <div v-for="n in getFullBoxes(resultData.region1_copies)" :key="'full1-'+n" class="waffle-box full bg-deep-purple-accent-2">
                      <v-icon size="small" color="white">mdi-gamepad-variant</v-icon>
                    </div>
                    <div v-if="resultData.region1_copies % 1 !== 0" class="waffle-box partial bg-grey-lighten-2">
                      <div class="partial-fill bg-deep-purple-accent-2" :style="{ height: getPartialBoxHeight(resultData.region1_copies) }"></div>
                    </div>
                  </div>
                </v-col>

                <v-col cols="12" md="6">
                  <div class="text-center mb-4 d-flex flex-column align-center">
                    <v-avatar size="48" rounded="sm" class="mb-3 elevation-8" style="border: 1px solid rgba(255,255,255,0.2);">
                      <img :src="`https://flagcdn.com/w80/${region2}.png`" style="width: 100%; height: 100%; object-fit: cover;">
                    </v-avatar>
                    <h3 class="text-h5 font-weight-bold text-cyan-accent-3">{{ region2.toUpperCase() }}</h3>
                    <div class="text-h3 font-weight-black mt-2">{{ resultData.region2_copies }} <span class="text-subtitle-1">kopii</span></div>
                    <div class="text-body-2 text-grey">Cena: {{ resultData.region2_price }} {{ resultData.region2_currency }}</div>
                  </div>
                  <div class="waffle-container">
                    <div v-for="n in getFullBoxes(resultData.region2_copies)" :key="'full2-'+n" class="waffle-box full bg-cyan-accent-4">
                      <v-icon size="small" color="black">mdi-gamepad-variant</v-icon>
                    </div>
                    <div v-if="resultData.region2_copies % 1 !== 0" class="waffle-box partial bg-grey-lighten-2">
                      <div class="partial-fill bg-cyan-accent-4" :style="{ height: getPartialBoxHeight(resultData.region2_copies) }"></div>
                    </div>
                  </div>
                </v-col>
              </v-row>

              <v-divider class="my-10"></v-divider>

              <v-row>
                <v-col cols="12" md="6">
                  <h3 class="text-h5 font-weight-bold mb-6 text-center text-amber-accent-2">Indeks Koszyka Gracza</h3>
                  <v-card variant="tonal" class="pa-5 rounded-lg" color="blue-grey-darken-3">
                    <p class="text-body-2 text-grey-lighten-1 mb-4 text-center">Analiza % pensji potrzebnego na zakup koszyka 5 flagowych gier (GTA V, Wiedźmin 3, Cyberpunk 2077, RDR 2, BG3).</p>

                    <div class="mb-4">
                      <div class="d-flex justify-space-between text-caption mb-1 font-weight-bold text-deep-purple-accent-1">
                        <span>{{ region1.toUpperCase() }} ({{ basketData.region1_basket_price }} {{ resultData.region1_currency }})</span>
                        <span>{{ basketData.region1_pct }}% pensji</span>
                      </div>
                      <v-progress-linear :model-value="basketData.region1_pct" color="deep-purple-accent-2" height="18" rounded></v-progress-linear>
                    </div>

                    <div>
                      <div class="d-flex justify-space-between text-caption mb-1 font-weight-bold text-cyan-accent-3">
                        <span>{{ region2.toUpperCase() }} ({{ basketData.region2_basket_price }} {{ resultData.region2_currency }})</span>
                        <span>{{ basketData.region2_pct }}% pensji</span>
                      </div>
                      <v-progress-linear :model-value="basketData.region2_pct" color="cyan-accent-4" height="18" rounded></v-progress-linear>
                    </div>
                  </v-card>
                </v-col>

                <v-col cols="12" md="6">
                  <h3 class="text-h5 font-weight-bold mb-6 text-center text-amber-accent-2">Trend Historyczny (2019-2024)</h3>
                  <v-card variant="tonal" class="pa-5 rounded-lg" color="blue-grey-darken-3">
                    <p class="text-body-2 text-grey-lighten-1 mb-4 text-center">Zmiana ilości gier w koszyku możliwych do zakupu na przestrzeni lat (Drill-down).</p>
                    <div style="height: 200px;">
                      <Line :data="historyData" :options="chartOptions" />
                    </div>
                  </v-card>
                </v-col>
              </v-row>

            </v-card>
          </div>
        </v-expand-transition>
      </v-container>
    </v-main>
  </v-app>
</template>

<style scoped>
.app-background {
  background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
  min-height: 100vh;
}

.glass-card {
  background: rgba(30, 30, 30, 0.7) !important;
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.gradient-text {
  background: linear-gradient(to right, #00f2fe 0%, #4facfe 100%);
  -webkit-background-clip: text;
  color: transparent;
}

.featured-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid rgba(255,255,255,0.1);
}

.featured-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 10px 20px rgba(0, 242, 254, 0.2) !important;
}

.game-title-overlay {
  background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 100%);
}

.waffle-container {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  align-content: flex-start;
  min-height: 200px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.waffle-box {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  position: relative;
  overflow: hidden;
}

.waffle-box.partial {
  align-items: flex-end;
}

.partial-fill {
  width: 100%;
  bottom: 0;
  position: absolute;
}
</style>