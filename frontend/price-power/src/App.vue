<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import { Line, Radar, Doughnut, Bar } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, PointElement, LineElement, BarElement, CategoryScale, LinearScale, RadialLinearScale, ArcElement, Filler } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, PointElement, LineElement, BarElement, CategoryScale, LinearScale, RadialLinearScale, ArcElement, Filler)

const gameId = ref<any>(null)
const gameHistoryData = ref<any>(null)
const chartMode = ref('basket')
const searchQuery = ref('')
const isSearching = ref(false)
const searchResults = ref<any[]>([])
const currentChartData = computed(() => {
  return chartMode.value === 'basket' ? historyData.value : gameHistoryData.value
})
let searchTimeout: any = null
const simMonths = ref(1)
const subSimData = ref<any>(null)

const calculateSubSim = async () => {
  if (!resultData.value) return
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/subscription-sim', {
      params: {
        region1: region1.value,
        region2: region2.value,
        app_price1: resultData.value.region1_price,
        app_price2: resultData.value.region2_price,
        months: simMonths.value
      }
    })
    subSimData.value = res.data
  } catch (error) {
  }
}

watch(simMonths, calculateSubSim)
const customBasket = ref<any[]>([])
const basketSearchQuery = ref('')
const basketSearchResults = ref<any[]>([])
const isBasketSearching = ref(false)
const customBasketData = ref<any>(null)
const isCustomBasketLoading = ref(false)
let basketSearchTimeout: any = null
const storeType = ref('keyshops')
const isInitialLoading = ref(true)
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
const radarData = ref<any>(null)
const doughnutData1 = ref<any>(null)
const doughnutData2 = ref<any>(null)
const barData = ref<any>(null)
const gameDetails = ref<any>(null)

let rotationInterval: any = null

const bgCanvas = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let particlesArray: any[] = []
let animationFrameId: number

const mouse = {
  x: null as number | null,
  y: null as number | null,
  isDown: false,
  grabbedParticle: null as Particle | null
}

const simLiving1 = ref(40)
const simOther1 = ref(30)
const simLiving2 = ref(40)
const simOther2 = ref(30)

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
  isInitialLoading.value = true
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
    console.error("Błąd pobierania danych:", error)
  } finally {
    isInitialLoading.value = false
  }
}

const createDoughnut = (gamePct: string, color: string, living: number = 40, other: number = 30) => {
  const gPct = parseFloat(gamePct)
  return {
    labels: ['Gra', 'Mieszkanie', 'Życie', 'Oszczędności'],
    datasets: [{
      backgroundColor: [color, '#37474F', '#455A64', '#263238'],
      borderWidth: 0,
      data: [gPct, living, other, Math.max(0, 100 - gPct - living - other)]
    }]
  }
}

watch([simLiving1, simOther1, simLiving2, simOther2], () => {
  if (!resultData.value) return
  doughnutData1.value = createDoughnut(resultData.value.pct1, '#7C4DFF', simLiving1.value, simOther1.value)
  doughnutData2.value = createDoughnut(resultData.value.pct2, '#00E5FF', simLiving2.value, simOther2.value)
})

const currencyRates: Record<string, number> = {
  'USD': 1.0,
  'EUR': 0.92,
  'PLN': 3.98,
  'GBP': 0.79,
  'AUD': 1.53,
  'CAD': 1.36,
  'CHF': 0.90,
  'DKK': 6.87,
  'NOK': 10.8,
  'SEK': 10.6,
  'BRL': 5.05
}

const expectedCurrencyMap: Record<string, string> = {
    "pl": "PLN", "de": "EUR", "us": "USD", "gb": "GBP", "fr": "EUR",
    "au": "AUD", "be": "EUR", "br": "BRL", "ca": "CAD", "ch": "CHF",
    "dk": "DKK", "es": "EUR", "eu": "EUR", "fi": "EUR", "ie": "EUR",
    "it": "EUR", "nl": "EUR", "no": "NOK", "se": "SEK"
}

watch(basketSearchQuery, (val) => {
  if (typeof val !== 'string' || !val || val.length < 3) {
    basketSearchResults.value = []
    return
  }
  if (basketSearchTimeout) clearTimeout(basketSearchTimeout)
  basketSearchTimeout = setTimeout(async () => {
    isBasketSearching.value = true
    try {
      const response = await axios.get(`http://127.0.0.1:8000/api/search?query=${val}`)
      basketSearchResults.value = response.data.games
    } catch (error) {
    } finally {
      isBasketSearching.value = false
    }
  }, 500)
})

const addToBasket = (game: any) => {
  if (game && !customBasket.value.find(g => g.value === game.value)) {
    customBasket.value.push(game)
  }
  basketSearchQuery.value = ''
}

const removeFromBasket = (appId: string) => {
  customBasket.value = customBasket.value.filter(g => g.value !== appId)
  if (customBasket.value.length === 0) {
    customBasketData.value = null
  }
}

const calculateCustomBasket = async () => {
  if (customBasket.value.length === 0) return
  isCustomBasketLoading.value = true
  try {
    const ids = customBasket.value.map(g => g.value).join(',')
    const res = await axios.get('http://127.0.0.1:8000/api/custom-basket', {
      params: { region1: region1.value, region2: region2.value, wage1: wage1.value, wage2: wage2.value, app_ids: ids }
    })
    customBasketData.value = res.data
  } catch (error) {
  } finally {
    isCustomBasketLoading.value = false
  }
}

const compareData = async () => {
  if (!gameId.value) return
  isLoading.value = true

  const actualAppId = typeof gameId.value === 'object' ? gameId.value.value : gameId.value

  try {
   const [compRes, histRes, basketRes, detailsRes, gameHistRes] = await Promise.all([
      axios.get('http://127.0.0.1:8000/api/compare', {
        params: {
          app_id: actualAppId,
          region1: region1.value,
          region2: region2.value,
          wage1: wage1.value,
          wage2: wage2.value,
          store_type: storeType.value
        }
      }),
      axios.get('http://127.0.0.1:8000/api/dw/history', {
        params: { region1: region1.value, region2: region2.value }
      }),
      axios.get('http://127.0.0.1:8000/api/dw/basket', {
        params: { region1: region1.value, region2: region2.value, wage1: wage1.value, wage2: wage2.value }
      }),
      axios.get('http://127.0.0.1:8000/api/game-details', {
        params: { app_id: actualAppId }
      }),
      axios.get('http://127.0.0.1:8000/api/game-history', {
        params: { app_id: actualAppId, region1: region1.value, region2: region2.value }
      })
    ])

    gameDetails.value = detailsRes.data

    let price1 = compRes.data.region1_price
    let currency1 = compRes.data.region1_currency
    const expectedCurr1 = expectedCurrencyMap[region1.value.toLowerCase()]

    if (currency1 !== expectedCurr1 && currencyRates[expectedCurr1] && currencyRates[currency1]) {
       const normalizedToUsd = price1 / currencyRates[currency1]
       price1 = normalizedToUsd * currencyRates[expectedCurr1]
       currency1 = expectedCurr1
    }

    let price2 = compRes.data.region2_price
    let currency2 = compRes.data.region2_currency
    const expectedCurr2 = expectedCurrencyMap[region2.value.toLowerCase()]

    if (currency2 !== expectedCurr2 && currencyRates[expectedCurr2] && currencyRates[currency2]) {
       const normalizedToUsd = price2 / currencyRates[currency2]
       price2 = normalizedToUsd * currencyRates[expectedCurr2]
       currency2 = expectedCurr2
    }

    compRes.data.region1_price = Number(price1.toFixed(2))
    compRes.data.region1_currency = currency1
    compRes.data.region2_price = Number(price2.toFixed(2))
    compRes.data.region2_currency = currency2

    compRes.data.region1_copies = wage1.value / compRes.data.region1_price
    compRes.data.region2_copies = wage2.value / compRes.data.region2_price

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
    gameHistoryData.value = {
      labels: gameHistRes.data.labels,
      datasets: [
        {
          label: region1.value.toUpperCase(),
          borderColor: '#7C4DFF',
          backgroundColor: '#7C4DFF',
          data: gameHistRes.data.region1_history,
          tension: 0.4,
          borderWidth: 3
        },
        {
          label: region2.value.toUpperCase(),
          borderColor: '#00E5FF',
          backgroundColor: '#00E5FF',
          data: gameHistRes.data.region2_history,
          tension: 0.4,
          borderWidth: 3
        }
      ]
    }

    radarData.value = {
      labels: ['Siła Nabywcza', 'Przystępność Koszyka', 'Czas Wolny', 'Tania Gra'],
      datasets: [
        {
          label: region1.value.toUpperCase(),
          backgroundColor: 'rgba(124, 77, 255, 0.4)',
          borderColor: '#7C4DFF',
          pointBackgroundColor: '#7C4DFF',
          data: [
            Math.min(copies1, 100),
            Math.max(100 - basketRes.data.region1_pct, 0),
            Math.min(100 / (parseFloat(resultData.value.hours1) || 1) * 10, 100),
            Math.max(100 - parseFloat(resultData.value.pct1) * 10, 0)
          ]
        },
        {
          label: region2.value.toUpperCase(),
          backgroundColor: 'rgba(0, 229, 255, 0.4)',
          borderColor: '#00E5FF',
          pointBackgroundColor: '#00E5FF',
          data: [
            Math.min(copies2, 100),
            Math.max(100 - basketRes.data.region2_pct, 0),
            Math.min(100 / (parseFloat(resultData.value.hours2) || 1) * 10, 100),
            Math.max(100 - parseFloat(resultData.value.pct2) * 10, 0)
          ]
        }
      ]
    }

    simLiving1.value = 40
    simOther1.value = 30
    simLiving2.value = 40
    simOther2.value = 30

    doughnutData1.value = createDoughnut(resultData.value.pct1, '#7C4DFF', simLiving1.value, simOther1.value)
    doughnutData2.value = createDoughnut(resultData.value.pct2, '#00E5FF', simLiving2.value, simOther2.value)

    const ppiMap: Record<string, number> = {
      'us': 1.0, 'ch': 0.6, 'de': 1.5, 'gb': 1.2, 'fr': 1.6,
      'au': 1.1, 'be': 1.4, 'br': 6.0, 'ca': 1.1, 'dk': 0.9,
      'es': 2.0, 'eu': 1.5, 'fi': 1.3, 'ie': 1.2, 'it': 1.8,
      'nl': 1.3, 'no': 0.8, 'pl': 4.5, 'se': 1.0, 'tr': 8.5
    };

    const r1Code = region1.value.toLowerCase();
    const r1PPI = ppiMap[r1Code] || 1.5;
    const baseUSHours = (parseFloat(resultData.value.hours1) || 1) / r1PPI;

    const r1Title = availableRegions.find(r => r.value === region1.value)?.title.split(' ')[0] || region1.value.toUpperCase();
    const r2Title = availableRegions.find(r => r.value === region2.value)?.title.split(' ')[0] || region2.value.toUpperCase();
    const rawWages = [
      { code: 'TR', name: 'Turcja', val: baseUSHours * 8.5 },
      { code: region1.value.toUpperCase(), name: r1Title, val: parseFloat(resultData.value.hours1) || 0 },
      { code: 'BR', name: 'Brazylia', val: baseUSHours * 6.0 },
      { code: region2.value.toUpperCase(), name: r2Title, val: parseFloat(resultData.value.hours2) || 0 },
      { code: 'US', name: 'USA', val: baseUSHours * 1.0 },
      { code: 'CH', name: 'Szwajcaria', val: baseUSHours * 0.6 }
    ];

    // Usuwamy duplikaty (gdyby ktoś wybrał np. USA w select boxie)
    const uniqueWages: any[] = [];
    const seenCodes = new Set();
    for (const w of rawWages) {
      if (!seenCodes.has(w.code)) {
        uniqueWages.push(w);
        seenCodes.add(w.code);
      }
    }

    uniqueWages.sort((a, b) => b.val - a.val);

    barData.value = {
      labels: uniqueWages.map(w => w.name),
      datasets: [{
        backgroundColor: uniqueWages.map(w => w.code === region1.value.toUpperCase() ? '#7C4DFF' : w.code === region2.value.toUpperCase() ? '#00E5FF' : 'rgba(255,255,255,0.2)'),
        borderRadius: 6,
        data: uniqueWages.map(w => Number(w.val.toFixed(1)))
      }]
    }

  } catch (error) {
  }
  finally {
    await calculateSubSim()
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

const radarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { labels: { color: 'white' } } },
  scales: {
    r: {
      grid: { color: 'rgba(255,255,255,0.1)' },
      pointLabels: { color: '#ccc', font: { size: 12 } },
      ticks: { display: false },
      angleLines: { color: 'rgba(255,255,255,0.1)' }
    }
  }
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  cutout: '70%'
}

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#ccc' } },
    x: { grid: { display: false }, ticks: { color: '#ccc' } }
  }
}

class Particle {
  x: number
  y: number
  baseX: number
  baseY: number
  directionX: number
  directionY: number
  size: number
  color: string

  constructor(x: number, y: number, directionX: number, directionY: number, size: number) {
    this.x = x
    this.y = y
    this.baseX = x
    this.baseY = y
    this.directionX = directionX
    this.directionY = directionY
    this.size = size
    this.color = '#00E5FF'
  }

  draw() {
    if (!ctx) return
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false)
    ctx.fillStyle = this.color
    ctx.fill()
  }

  update() {
    if (!bgCanvas.value) return

    if (mouse.grabbedParticle === this && mouse.x != null && mouse.y != null) {
      this.x = mouse.x
      this.y = mouse.y
      this.color = '#7C4DFF'
    } else {
      if (this.x > bgCanvas.value.width || this.x < 0) {
        this.directionX = -this.directionX
      }
      if (this.y > bgCanvas.value.height || this.y < 0) {
        this.directionY = -this.directionY
      }
      this.x += this.directionX
      this.y += this.directionY

      if (mouse.x != null && mouse.y != null) {
        let dx = mouse.x - this.x
        let dy = mouse.y - this.y
        let distance = Math.sqrt(dx * dx + dy * dy)

        if (distance < 60) {
           this.color = '#00f2fe'
           ctx!.beginPath()
           ctx!.arc(this.x, this.y, this.size + 2, 0, Math.PI * 2, false)
           ctx!.fillStyle = 'rgba(0, 242, 254, 0.3)'
           ctx!.fill()
        } else {
           this.color = '#00E5FF'
        }
      } else {
         this.color = '#00E5FF'
      }
    }
    this.draw()
  }
}

const initPlexus = () => {
  if (!bgCanvas.value) return
  ctx = bgCanvas.value.getContext('2d')
  bgCanvas.value.width = window.innerWidth
  bgCanvas.value.height = window.innerHeight
  particlesArray = []
  const numberOfParticles = Math.floor((bgCanvas.value.height * bgCanvas.value.width) / 7000)
  for (let i = 0; i < numberOfParticles; i++) {
    const size = (Math.random() * 2.5) + 1.5
    const x = (Math.random() * ((window.innerWidth - size * 2) - (size * 2)) + size * 2)
    const y = (Math.random() * ((window.innerHeight - size * 2) - (size * 2)) + size * 2)
    const directionX = (Math.random() * 1) - 0.5
    const directionY = (Math.random() * 1) - 0.5
    particlesArray.push(new Particle(x, y, directionX, directionY, size))
  }
}

const connectPlexus = () => {
  for (let a = 0; a < particlesArray.length; a++) {
    for (let b = a + 1; b < particlesArray.length; b++) {
      const dx = particlesArray[a].x - particlesArray[b].x
      const dy = particlesArray[a].y - particlesArray[b].y
      const distance = (dx * dx) + (dy * dy)

      if (distance < 18000) {
        let opacity = 1 - (distance / 18000)

        ctx!.strokeStyle = `rgba(0, 229, 255, ${opacity * 0.4})`
        if(mouse.grabbedParticle === particlesArray[a] || mouse.grabbedParticle === particlesArray[b]) {
           ctx!.strokeStyle = `rgba(124, 77, 255, ${opacity * 0.8})`
        }
        ctx!.lineWidth = 1
        ctx!.beginPath()
        ctx!.moveTo(particlesArray[a].x, particlesArray[a].y)
        ctx!.lineTo(particlesArray[b].x, particlesArray[b].y)
        ctx!.stroke()

        for (let c = b + 1; c < particlesArray.length; c++) {
          const dx2 = particlesArray[b].x - particlesArray[c].x
          const dy2 = particlesArray[b].y - particlesArray[c].y
          const distance2 = (dx2 * dx2) + (dy2 * dy2)

          if (distance2 < 18000) {
            const dx3 = particlesArray[a].x - particlesArray[c].x
            const dy3 = particlesArray[a].y - particlesArray[c].y
            const distance3 = (dx3 * dx3) + (dy3 * dy3)

            if (distance3 < 18000) {
              let triangleOpacity = Math.min(
                1 - (distance / 18000),
                1 - (distance2 / 18000),
                1 - (distance3 / 18000)
              )

              let color = `rgba(0, 229, 255, ${triangleOpacity * 0.1})`

              if (mouse.grabbedParticle === particlesArray[a] ||
                  mouse.grabbedParticle === particlesArray[b] ||
                  mouse.grabbedParticle === particlesArray[c]) {
                 color = `rgba(124, 77, 255, ${triangleOpacity * 0.25})`
              }

              ctx!.beginPath()
              ctx!.moveTo(particlesArray[a].x, particlesArray[a].y)
              ctx!.lineTo(particlesArray[b].x, particlesArray[b].y)
              ctx!.lineTo(particlesArray[c].x, particlesArray[c].y)
              ctx!.closePath()
              ctx!.fillStyle = color
              ctx!.fill()
            }
          }
        }
      }
    }
  }
}

const animatePlexus = () => {
  if (!bgCanvas.value || !ctx) return
  animationFrameId = requestAnimationFrame(animatePlexus)
  ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)
  for (let i = 0; i < particlesArray.length; i++) {
    particlesArray[i].update()
  }
  connectPlexus()
}

const handleResize = () => {
  if (!bgCanvas.value) return
  bgCanvas.value.width = window.innerWidth
  bgCanvas.value.height = window.innerHeight
  initPlexus()
}

const handleMouseMove = (event: MouseEvent) => {
  mouse.x = event.clientX
  mouse.y = event.clientY
}

const handleMouseDown = () => {
  mouse.isDown = true
  if (mouse.x == null || mouse.y == null) return

  let closestParticle = null
  let minDistance = 60

  for (let i = 0; i < particlesArray.length; i++) {
    let dx = mouse.x - particlesArray[i].x
    let dy = mouse.y - particlesArray[i].y
    let distance = Math.sqrt(dx * dx + dy * dy)

    if (distance < minDistance) {
      closestParticle = particlesArray[i]
      minDistance = distance
    }
  }

  if (closestParticle) {
    mouse.grabbedParticle = closestParticle
  }
}

const handleMouseUp = () => {
  mouse.isDown = false
  mouse.grabbedParticle = null
}

const handleMouseLeave = () => {
  mouse.x = null
  mouse.y = null
  mouse.isDown = false
  mouse.grabbedParticle = null
}

onMounted(() => {
  fetchInitialData()
  initPlexus()
  animatePlexus()
  window.addEventListener('resize', handleResize)
  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('mousedown', handleMouseDown)
  window.addEventListener('mouseup', handleMouseUp)
  document.body.addEventListener('mouseleave', handleMouseLeave)
})

onUnmounted(() => {
  if (rotationInterval) clearInterval(rotationInterval)
  cancelAnimationFrame(animationFrameId)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mousedown', handleMouseDown)
  window.removeEventListener('mouseup', handleMouseUp)
  document.body.removeEventListener('mouseleave', handleMouseLeave)
})
</script>

  <template>
    <v-app class="app-background">
      <canvas ref="bgCanvas" class="plexus-canvas"></canvas>
      <v-main style="position: relative; z-index: 1;">
        <v-container class="py-10">

          <div class="text-center mb-12 mt-4 position-relative">
            <div class="header-glow"></div>
            <div class="d-flex justify-center align-center mb-4 flex-wrap">
              <v-icon size="56" color="cyan-accent-3" class="mr-sm-4 mb-2 mb-sm-0 header-icon d-none d-sm-flex">mdi-database-search</v-icon>
              <h1 class="text-h2 font-weight-black text-uppercase animated-gradient-text mb-0">
                Price Power <span class="text-cyan-accent-3"></span>
              </h1>
              <v-icon size="56" color="deep-purple-accent-2" class="ml-sm-4 mb-2 mb-sm-0 header-icon d-none d-sm-flex">mdi-controller-classic</v-icon>
            </div>
            <p class="text-h6 text-grey-lighten-1 mb-8 font-weight-regular" style="letter-spacing: 1px;">
              Zaawansowana analityka wielowymiarowa siły nabywczej graczy
            </p>
            <div class="d-flex justify-center gap-4 flex-wrap">
              <v-chip color="success" variant="elevated" size="small" prepend-icon="mdi-check-circle" class="glass-chip font-weight-bold ma-1">
                Silnik OLAP: Aktywny
              </v-chip>
              <v-chip color="cyan-accent-4" variant="elevated" size="small" prepend-icon="mdi-database-sync" class="glass-chip font-weight-bold ma-1">
                Hurtownia: Zsynchronizowana
              </v-chip>
              <v-chip color="deep-purple-accent-1" variant="elevated" size="small" prepend-icon="mdi-chart-timeline-variant" class="glass-chip font-weight-bold ma-1">
                Analiza Time-Series: Gotowa
              </v-chip>
            </div>
          </div>

<v-row class="mb-8" justify="center">
<template v-if="isInitialLoading">
            <v-col cols="6" sm="4" md="3" v-for="i in 8" :key="'skel-' + i">
              <v-card class="rounded-xl overflow-hidden" elevation="12" color="rgba(255,255,255,0.05)">
                <v-skeleton-loader
                  type="image"
                  height="120"
                  theme="dark"
                  style="background: transparent;"
                ></v-skeleton-loader>
              </v-card>
            </v-col>
          </template>

          <template v-else>
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
          </template>
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

<div class="d-flex justify-center align-center mb-8 gap-4 flex-wrap" style="gap: 20px;">
            <v-btn-toggle v-model="storeType" color="deep-purple-accent-1" rounded="pill" mandatory group class="elevation-4" style="background: rgba(0,0,0,0.4);">
              <v-btn value="keyshops" class="px-6 font-weight-bold">
                <v-icon left class="mr-2">mdi-key-variant</v-icon> Key Shopy
              </v-btn>
              <v-btn value="retail" class="px-6 font-weight-bold">
                <v-icon left class="mr-2">mdi-store</v-icon> Oficjalne Sklepy
              </v-btn>
            </v-btn-toggle>

            <v-btn-toggle v-model="wageType" color="cyan-accent-3" rounded="pill" mandatory group class="elevation-4" style="background: rgba(0,0,0,0.4);">
              <v-btn value="min" class="px-6 font-weight-bold">
                <v-icon left class="mr-2">mdi-cash-minus</v-icon> Pensja Minimalna
              </v-btn>
              <v-btn value="avg" class="px-6 font-weight-bold">
                <v-icon left class="mr-2">mdi-cash-multiple</v-icon> Pensja Średnia
              </v-btn>
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

            <v-btn block size="x-large" color="cyan-darken-3" class="mt-8 rounded-lg font-weight-bold pulse-button" elevation="8" @click="compareData" :loading="isLoading" :disabled="!gameId">
              <v-icon left class="mr-2">mdi-database-search</v-icon> Wykonaj Analizę
            </v-btn>
          </v-card>
<v-expand-transition>
            <div v-if="isLoading" class="mt-10">
              <v-card class="pa-8 rounded-xl glass-card mx-auto" max-width="1200" theme="dark">
                <v-row align="center" class="mb-8">
                  <v-col cols="12" sm="4">
                    <v-skeleton-loader type="image" height="200" color="rgba(255,255,255,0.05)"></v-skeleton-loader>
                  </v-col>
                  <v-col cols="12" sm="8">
                    <v-skeleton-loader type="heading, paragraph" color="rgba(255,255,255,0.05)"></v-skeleton-loader>
                  </v-col>
                </v-row>
                <v-skeleton-loader type="table-heading, list-item-two-line, image" color="rgba(255,255,255,0.05)"></v-skeleton-loader>
              </v-card>
            </div>
            <div v-else-if="resultData" class="mt-10">
              <v-card class="pa-8 rounded-xl glass-card mx-auto" max-width="1200" theme="dark">

                <v-row class="mb-10 mt-2">
                  <v-col cols="12" md="7">
                    <div v-if="gameDetails?.trailer" class="rounded-lg overflow-hidden elevation-10" style="position: relative; padding-top: 56.25%; border: 1px solid rgba(255,255,255,0.1);">
                      <video autoplay loop muted playsinline style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover;">
                        <source :src="gameDetails.trailer" type="video/webm">
                      </video>
                    </div>
                    <v-img v-else :src="resultData?.image" class="rounded-lg elevation-10" cover aspect-ratio="16/9" style="border: 1px solid rgba(255,255,255,0.1);"></v-img>
                  </v-col>

                  <v-col cols="12" md="5" class="d-flex flex-column justify-center pl-md-6">
                    <h2 class="text-h3 font-weight-black text-cyan-accent-1 mb-3">{{ resultData?.game_title }}</h2>
                    <p class="text-body-2 text-grey-lighten-1 mb-6" v-html="gameDetails?.description || 'Szczegółowy raport siły nabywczej na podstawie wybranego tytułu.'"></p>

                    <v-row density="comfortable">
                      <v-col cols="6">
                        <v-card variant="tonal" color="light-green-accent-3" class="pa-4 rounded-lg text-center h-100 d-flex flex-column justify-center">
                          <div class="text-caption text-uppercase mb-1 font-weight-bold">Aktualnie Gra (Steam)</div>
                          <div class="text-h5 font-weight-black">{{ gameDetails?.players ? gameDetails.players.toLocaleString() : '0' }}</div>
                        </v-card>
                      </v-col>
                      <v-col cols="6">
                        <v-card variant="tonal" color="amber-accent-3" class="pa-4 rounded-lg text-center h-100 d-flex flex-column justify-center">
                          <div class="text-caption text-uppercase mb-1 font-weight-bold">Metacritic</div>
                          <div class="text-h5 font-weight-black">{{ gameDetails?.metacritic || 'Brak' }}</div>
                        </v-card>
                      </v-col>
                      <v-col cols="12">
                        <v-card variant="tonal" color="blue-grey-lighten-2" class="pa-3 rounded-lg text-center mt-2">
                          <div class="text-caption text-uppercase mb-1 font-weight-bold">Gatunek</div>
                          <div class="text-subtitle-2">{{ gameDetails?.genres ? gameDetails.genres.join(' • ') : 'Brak danych' }}</div>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-col>
                </v-row>

                <v-divider class="mb-8"></v-divider>

                <v-row>
                  <v-col cols="12" md="6">
                    <div class="text-center mb-4 d-flex flex-column align-center">
                      <div class="mb-3" style="width: 105px; height: 105px; filter: drop-shadow(0px 0px 10px rgba(124, 77, 255, 0.6));">
                        <div :style="`
                          width: 100%;
                          height: 100%;
                          background-image: url('https://flagcdn.com/w160/${region1}.png');
                          background-size: cover;
                          background-position: center;
                          -webkit-mask-image: url('https://cdn.jsdelivr.net/gh/djaiss/mapsicon@master/all/${region1}/vector.svg');
                          mask-image: url('https://cdn.jsdelivr.net/gh/djaiss/mapsicon@master/all/${region1}/vector.svg');
                          -webkit-mask-size: contain;
                          mask-size: contain;
                          -webkit-mask-repeat: no-repeat;
                          mask-repeat: no-repeat;
                          -webkit-mask-position: center;
                          mask-position: center;
                        `"></div>
                      </div>
                      <h3 class="text-h5 font-weight-bold text-deep-purple-accent-1">{{ region1.toUpperCase() }}</h3>
                      <div class="text-h3 font-weight-black mt-2">{{ Number(resultData?.region1_copies).toFixed(1) }} <span class="text-subtitle-1">kopii</span></div>
                      <div class="text-body-2 text-grey">Cena: {{ resultData?.region1_price }} {{ resultData?.region1_currency }}</div>
                    </div>
                    <div class="waffle-container">
                      <div v-for="n in getFullBoxes(resultData?.region1_copies || 0)" :key="'full1-'+n" class="waffle-box full bg-deep-purple-accent-2" :style="{ animationDelay: `${n * 0.015}s` }">
                        <v-icon size="small" color="white">mdi-gamepad-variant</v-icon>
                      </div>
                      <div v-if="(resultData?.region1_copies || 0) % 1 !== 0" class="waffle-box partial bg-grey-lighten-2" :style="{ animationDelay: `${getFullBoxes(resultData?.region1_copies || 0) * 0.015}s` }">
                        <div class="partial-fill bg-deep-purple-accent-2" :style="{ height: getPartialBoxHeight(resultData?.region1_copies || 0) }"></div>
                      </div>
                    </div>
                  </v-col>

                  <v-col cols="12" md="6">
                    <div class="text-center mb-4 d-flex flex-column align-center">
                      <div class="mb-3" style="width: 105px; height: 105px; filter: drop-shadow(0px 0px 10px rgba(0, 229, 255, 0.6));">
                        <div :style="`
                          width: 100%;
                          height: 100%;
                          background-image: url('https://flagcdn.com/w160/${region2}.png');
                          background-size: cover;
                          background-position: center;
                          -webkit-mask-image: url('https://cdn.jsdelivr.net/gh/djaiss/mapsicon@master/all/${region2}/vector.svg');
                          mask-image: url('https://cdn.jsdelivr.net/gh/djaiss/mapsicon@master/all/${region2}/vector.svg');
                          -webkit-mask-size: contain;
                          mask-size: contain;
                          -webkit-mask-repeat: no-repeat;
                          mask-repeat: no-repeat;
                          -webkit-mask-position: center;
                          mask-position: center;
                        `"></div>
                      </div>
                      <h3 class="text-h5 font-weight-bold text-cyan-accent-3">{{ region2.toUpperCase() }}</h3>
                      <div class="text-h3 font-weight-black mt-2">{{ Number(resultData?.region2_copies).toFixed(1) }} <span class="text-subtitle-1">kopii</span></div>
                      <div class="text-body-2 text-grey">Cena: {{ resultData?.region2_price }} {{ resultData?.region2_currency }}</div>
                    </div>
                    <div class="waffle-container">
                      <div v-for="n in getFullBoxes(resultData?.region2_copies || 0)" :key="'full2-'+n" class="waffle-box full bg-cyan-accent-4" :style="{ animationDelay: `${n * 0.015}s` }">
                        <v-icon size="small" color="black">mdi-gamepad-variant</v-icon>
                      </div>
                      <div v-if="(resultData?.region2_copies || 0) % 1 !== 0" class="waffle-box partial bg-grey-lighten-2" :style="{ animationDelay: `${getFullBoxes(resultData?.region2_copies || 0) * 0.015}s` }">
                        <div class="partial-fill bg-cyan-accent-4" :style="{ height: getPartialBoxHeight(resultData?.region2_copies || 0) }"></div>
                      </div>
                    </div>
                  </v-col>
                </v-row>

                <v-row class="mt-6">
                  <v-col cols="12" md="6">
                    <v-card variant="tonal" color="deep-purple-accent-2" class="pa-4 rounded-lg d-flex align-center">
                      <v-icon size="40" class="mr-4">mdi-clock-outline</v-icon>
                      <div>
                        <div class="text-caption text-uppercase">Czas pracy na 1 kopię</div>
                        <div class="text-h5 font-weight-bold">{{ resultData?.hours1 }} <span class="text-body-2">godzin</span></div>
                      </div>
                    </v-card>
                    <v-card variant="tonal" color="deep-purple-lighten-3" class="mt-4 pa-4 rounded-lg d-flex align-center">
                      <v-icon size="40" class="mr-4">mdi-calendar-today</v-icon>
                      <div>
                        <div class="text-caption text-uppercase">Kopie za 1 dzień pracy</div>
                        <div class="text-h5 font-weight-bold">{{ resultData?.daily_copies1 }} <span class="text-body-2">szt.</span></div>
                      </div>
                    </v-card>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-card variant="tonal" color="cyan-accent-4" class="pa-4 rounded-lg d-flex align-center">
                      <v-icon size="40" class="mr-4">mdi-clock-outline</v-icon>
                      <div>
                        <div class="text-caption text-uppercase">Czas pracy na 1 kopię</div>
                        <div class="text-h5 font-weight-bold">{{ resultData?.hours2 }} <span class="text-body-2">godzin</span></div>
                      </div>
                    </v-card>
                    <v-card variant="tonal" color="cyan-lighten-3" class="mt-4 pa-4 rounded-lg d-flex align-center">
                      <v-icon size="40" class="mr-4">mdi-calendar-today</v-icon>
                      <div>
                        <div class="text-caption text-uppercase">Kopie za 1 dzień pracy</div>
                        <div class="text-h5 font-weight-bold">{{ resultData?.daily_copies2 }} <span class="text-body-2">szt.</span></div>
                      </div>
                    </v-card>
                  </v-col>
                </v-row>

                <v-alert v-if="resultData?.multiplierMsg" icon="mdi-trophy" color="amber-darken-3" variant="tonal" class="mb-8 mt-5 rounded-lg" border="start">
                  <div class="text-h6 font-weight-bold">{{ resultData.multiplierMsg }}</div>
                </v-alert>

                <v-divider class="my-10"></v-divider>

                <v-row>
                  <v-col cols="12">
                    <h3 class="text-h5 font-weight-bold mb-6 text-center text-amber-accent-2">Twój Własny Koszyk Gier</h3>
                    <v-card variant="tonal" class="pa-5 rounded-lg" color="blue-grey-darken-3">
                      <v-autocomplete
                        v-model:search="basketSearchQuery"
                        :items="basketSearchQuery && basketSearchResults.length > 0 ? basketSearchResults : gamesList"
                        item-title="title"
                        item-value="value"
                        :loading="isBasketSearching"
                        label="Wyszukaj grę do koszyka..."
                        variant="outlined"
                        color="deep-purple-accent-1"
                        bg-color="rgba(0,0,0,0.4)"
                        prepend-inner-icon="mdi-cart-plus"
                        hide-no-data
                        return-object
                        @update:modelValue="addToBasket"
                      ></v-autocomplete>

                      <div class="d-flex flex-wrap gap-2 mb-6" v-if="customBasket.length > 0">
                        <v-chip
                          v-for="game in customBasket"
                          :key="game.value"
                          closable
                          @click:close="removeFromBasket(game.value)"
                          color="cyan-accent-3"
                          variant="elevated"
                          class="ma-1 text-black font-weight-bold"
                        >
                          {{ game.title }}
                        </v-chip>
                      </div>

                      <v-btn
                        block
                        color="deep-purple-accent-2"
                        @click="calculateCustomBasket"
                        :loading="isCustomBasketLoading"
                        :disabled="customBasket.length === 0"
                        class="mb-6 font-weight-bold"
                      >
                        Przelicz Własny Koszyk
                      </v-btn>

                      <div v-if="customBasketData">
                        <v-row>
                          <v-col cols="12" sm="6">
                            <div class="d-flex justify-space-between text-caption mb-1 font-weight-bold text-deep-purple-accent-1">
                              <span>{{ region1.toUpperCase() }} ({{ customBasketData.region1_basket_price }} {{ resultData?.region1_currency }})</span>
                              <span>{{ customBasketData.region1_pct }}% pensji</span>
                            </div>
                            <v-progress-linear :model-value="customBasketData.region1_pct" color="deep-purple-accent-2" height="18" rounded></v-progress-linear>
                          </v-col>
                          <v-col cols="12" sm="6">
                            <div class="d-flex justify-space-between text-caption mb-1 font-weight-bold text-cyan-accent-3">
                              <span>{{ region2.toUpperCase() }} ({{ customBasketData.region2_basket_price }} {{ resultData?.region2_currency }})</span>
                              <span>{{ customBasketData.region2_pct }}% pensji</span>
                            </div>
                            <v-progress-linear :model-value="customBasketData.region2_pct" color="cyan-accent-4" height="18" rounded></v-progress-linear>
                          </v-col>
                        </v-row>
                      </div>
                    </v-card>
                  </v-col>
                </v-row>

                <v-divider class="my-10"></v-divider>

                <v-row>
                  <v-col cols="12" md="6">
                    <h3 class="text-h5 font-weight-bold mb-6 text-center text-amber-accent-2">Indeks Koszyka Gracza</h3>
                    <v-card variant="tonal" class="pa-5 rounded-lg h-100" color="blue-grey-darken-3">
                      <p class="text-body-2 text-grey-lighten-1 mb-4 text-center">Analiza % pensji potrzebnego na zakup koszyka 5 flagowych gier (GTA V, Wiedźmin 3, Cyberpunk 2077, RDR 2, BG3).</p>
                      <div class="mb-4">
                        <div class="d-flex justify-space-between text-caption mb-1 font-weight-bold text-deep-purple-accent-1">
                          <span>{{ region1.toUpperCase() }} ({{ basketData?.region1_basket_price }} {{ resultData?.region1_currency }})</span>
                          <span>{{ basketData?.region1_pct }}% pensji</span>
                        </div>
                        <v-progress-linear :model-value="basketData?.region1_pct || 0" color="deep-purple-accent-2" height="18" rounded></v-progress-linear>
                      </div>

                      <div>
                        <div class="d-flex justify-space-between text-caption mb-1 font-weight-bold text-cyan-accent-3">
                          <span>{{ region2.toUpperCase() }} ({{ basketData?.region2_basket_price }} {{ resultData?.region2_currency }})</span>
                          <span>{{ basketData?.region2_pct }}% pensji</span>
                        </div>
                        <v-progress-linear :model-value="basketData?.region2_pct || 0" color="cyan-accent-4" height="18" rounded></v-progress-linear>
                      </div>
                    </v-card>
                  </v-col>

                  <v-col cols="12" md="6">
                    <h3 class="text-h5 font-weight-bold mb-6 text-center text-amber-accent-2">Analiza Historyczna</h3>
                    <v-card variant="tonal" class="pa-5 rounded-lg h-100" color="blue-grey-darken-3">
                      <div class="d-flex justify-center mb-6">
                        <v-btn-toggle v-model="chartMode" color="amber-accent-2" rounded="pill" mandatory group density="compact">
                          <v-btn value="basket" class="px-4 text-caption">Koszyk (Lata)</v-btn>
                          <v-btn value="game" class="px-4 text-caption">Wybrana Gra (Miesiące)</v-btn>
                        </v-btn-toggle>
                      </div>
                      <div style="height: 200px;">
                        <Line v-if="currentChartData" :data="currentChartData" :options="chartOptions" />
                      </div>
                    </v-card>
                  </v-col>
                </v-row>

                <v-divider class="my-10"></v-divider>

                <v-row>
                  <v-col cols="12">
                    <h3 class="text-h5 font-weight-bold mb-6 text-center text-amber-accent-2">Symulator Kosztu Alternatywnego (Zakup vs Abonament)</h3>
                    <v-card variant="tonal" class="pa-5 rounded-lg" color="blue-grey-darken-3">
                      <p class="text-body-2 text-grey-lighten-1 mb-6 text-center">Sprawdź, czy przy przewidywanym czasie gry bardziej opłaca się kupić grę, czy wykupić subskrypcję w danym regionie.</p>

                      <div class="px-md-10 mb-8">
                        <div class="d-flex justify-space-between text-caption font-weight-bold mb-2">
                          <span>1 miesiąc</span>
                          <span class="text-h6 text-amber-accent-2">{{ simMonths }} mies. gry</span>
                          <span>12 miesięcy</span>
                        </div>
                        <v-slider
                          v-model="simMonths"
                          color="amber-accent-2"
                          track-color="rgba(255,255,255,0.1)"
                          min="1"
                          max="12"
                          step="1"
                          hide-details
                        ></v-slider>
                      </div>

                      <v-row v-if="subSimData">
                        <v-col cols="12" sm="6">
                          <v-card class="pa-4 text-center rounded-lg border" :style="{ borderColor: subSimData.buy_better1 ? '#00E676' : '#FF1744', backgroundColor: 'rgba(0,0,0,0.2)' }">
                            <h4 class="text-subtitle-1 font-weight-bold text-deep-purple-accent-1 mb-2">{{ region1.toUpperCase() }}</h4>
                            <div class="d-flex justify-space-around my-4">
                              <div>
                                <div class="text-caption text-grey">Zakup Gry</div>
                                <div class="text-h6 font-weight-bold">{{ resultData.region1_price }} {{ resultData.region1_currency }}</div>
                              </div>
                              <div>
                                <div class="text-caption text-grey">Abonament ({{ simMonths }}m)</div>
                                <div class="text-h6 font-weight-bold">{{ subSimData.sub_cost1 }} {{ resultData.region1_currency }}</div>
                              </div>
                            </div>
                            <v-chip :color="subSimData.buy_better1 ? 'success' : 'error'" variant="flat" size="large" class="font-weight-bold text-uppercase mt-2">
                              <v-icon start>{{ subSimData.buy_better1 ? 'mdi-check-circle' : 'mdi-close-circle' }}</v-icon>
                              {{ subSimData.buy_better1 ? 'Zakup opłacalny' : 'Zostań przy abonamencie' }}
                            </v-chip>
                          </v-card>
                        </v-col>

                        <v-col cols="12" sm="6">
                          <v-card class="pa-4 text-center rounded-lg border" :style="{ borderColor: subSimData.buy_better2 ? '#00E676' : '#FF1744', backgroundColor: 'rgba(0,0,0,0.2)' }">
                            <h4 class="text-subtitle-1 font-weight-bold text-cyan-accent-3 mb-2">{{ region2.toUpperCase() }}</h4>
                            <div class="d-flex justify-space-around my-4">
                              <div>
                                <div class="text-caption text-grey">Zakup Gry</div>
                                <div class="text-h6 font-weight-bold">{{ resultData.region2_price }} {{ resultData.region2_currency }}</div>
                              </div>
                              <div>
                                <div class="text-caption text-grey">Abonament ({{ simMonths }}m)</div>
                                <div class="text-h6 font-weight-bold">{{ subSimData.sub_cost2 }} {{ resultData.region2_currency }}</div>
                              </div>
                            </div>
                            <v-chip :color="subSimData.buy_better2 ? 'success' : 'error'" variant="flat" size="large" class="font-weight-bold text-uppercase mt-2">
                              <v-icon start>{{ subSimData.buy_better2 ? 'mdi-check-circle' : 'mdi-close-circle' }}</v-icon>
                              {{ subSimData.buy_better2 ? 'Zakup opłacalny' : 'Zostań przy abonamencie' }}
                            </v-chip>
                          </v-card>
                        </v-col>
                      </v-row>
                    </v-card>
                  </v-col>
                </v-row>

                <v-divider class="my-10"></v-divider>

                <v-row>
                  <v-col cols="12" md="6">
                    <h3 class="text-h5 font-weight-bold mb-6 text-center text-amber-accent-2">Profil Wielowymiarowy</h3>
                    <v-card variant="tonal" class="pa-5 rounded-lg h-100" color="blue-grey-darken-3">
                      <p class="text-body-2 text-grey-lighten-1 mb-4 text-center">Zestawienie wskaźników ekonomicznych OLAP w skali znormalizowanej (0-100).</p>
                      <div style="height: 300px;">
                        <Radar v-if="radarData" :data="radarData" :options="radarOptions" />
                      </div>
                    </v-card>
                  </v-col>

                  <v-col cols="12" md="6">
                    <h3 class="text-h5 font-weight-bold mb-6 text-center text-amber-accent-2">Struktura Kosztów Życia</h3>
                    <v-card variant="tonal" class="pa-5 rounded-lg h-100" color="blue-grey-darken-3">
                      <p class="text-body-2 text-grey-lighten-1 mb-4 text-center">Symulacja podziału wypłaty z uwzględnieniem zakupu gry.</p>

                      <v-row>
                        <v-col cols="12" sm="6">
                          <div class="text-caption text-center mb-2 font-weight-bold text-deep-purple-accent-1">{{ region1.toUpperCase() }}</div>
                          <div style="height: 140px; position: relative;">
                            <Doughnut v-if="doughnutData1" :data="doughnutData1" :options="doughnutOptions" />
                            <div class="position-absolute d-flex align-center justify-center w-100 h-100" style="top: 0; left: 0; pointer-events: none;">
                              <span class="text-h6 font-weight-bold">{{ resultData?.pct1 }}%</span>
                            </div>
                          </div>
                          <div class="mt-4 px-2">
                            <v-slider v-model="simLiving1" color="#37474F" thumb-label max="80" min="10" step="1" hide-details class="mb-2">
                              <template v-slot:prepend><span class="text-caption" style="width: 70px;">Mieszkanie</span></template>
                            </v-slider>
                            <v-slider v-model="simOther1" color="#455A64" thumb-label max="80" min="10" step="1" hide-details>
                              <template v-slot:prepend><span class="text-caption" style="width: 70px;">Życie</span></template>
                            </v-slider>
                          </div>
                        </v-col>
                        <v-col cols="12" sm="6">
                          <div class="text-caption text-center mb-2 font-weight-bold text-cyan-accent-3">{{ region2.toUpperCase() }}</div>
                          <div style="height: 140px; position: relative;">
                            <Doughnut v-if="doughnutData2" :data="doughnutData2" :options="doughnutOptions" />
                            <div class="position-absolute d-flex align-center justify-center w-100 h-100" style="top: 0; left: 0; pointer-events: none;">
                              <span class="text-h6 font-weight-bold">{{ resultData?.pct2 }}%</span>
                            </div>
                          </div>
                          <div class="mt-4 px-2">
                            <v-slider v-model="simLiving2" color="#37474F" thumb-label max="80" min="10" step="1" hide-details class="mb-2">
                              <template v-slot:prepend><span class="text-caption" style="width: 70px;">Mieszkanie</span></template>
                            </v-slider>
                            <v-slider v-model="simOther2" color="#455A64" thumb-label max="80" min="10" step="1" hide-details>
                              <template v-slot:prepend><span class="text-caption" style="width: 70px;">Życie</span></template>
                            </v-slider>
                          </div>
                        </v-col>
                      </v-row>

                      <div class="d-flex justify-center flex-wrap gap-2 mt-6">
                        <v-chip size="small" color="#7C4DFF" variant="flat" class="ma-1">Gra</v-chip>
                        <v-chip size="small" color="#37474F" variant="flat" class="ma-1">Opłaty</v-chip>
                        <v-chip size="small" color="#455A64" variant="flat" class="ma-1">Życie</v-chip>
                        <v-chip size="small" color="#263238" variant="flat" class="ma-1">Oszczędności</v-chip>
                      </div>
                    </v-card>
                  </v-col>
                </v-row>

                <v-divider class="my-10"></v-divider>

                <v-row>
                  <v-col cols="12">
                    <h3 class="text-h5 font-weight-bold mb-6 text-center text-amber-accent-2">Globalny Benchmark (OLAP Slice)</h3>
                    <v-card variant="tonal" class="pa-5 rounded-lg" color="blue-grey-darken-3">
                      <p class="text-body-2 text-grey-lighten-1 mb-4 text-center">Ilość godzin pracy potrzebna na zakup tej samej gry w wybranych gospodarkach światowych.</p>
                      <div style="height: 300px;">
                        <Bar v-if="barData" :data="barData" :options="barOptions" />
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
    position: relative;
  }

  .plexus-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
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
    transform: scale(0);
    animation: pop-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
  }

  .waffle-box.partial {
    align-items: flex-end;
  }

  .partial-fill {
    width: 100%;
    bottom: 0;
    position: absolute;
  }

  .pulse-button {
    animation: pulse-glow 2s infinite;
  }

  @keyframes pulse-glow {
    0% { box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.4); }
    70% { box-shadow: 0 0 0 15px rgba(0, 229, 255, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 229, 255, 0); }
  }

  @keyframes pop-in {
    100% { transform: scale(1); }
  }

  .glass-card .v-card--variant-tonal {
    transition: all 0.3s ease;
  }

  .glass-card .v-card--variant-tonal:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0, 229, 255, 0.15) !important;
    background: rgba(255, 255, 255, 0.08) !important;
  }

  .animated-gradient-text {
    background: linear-gradient(270deg, #00E5FF, #4facfe, #7C4DFF, #00E5FF);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradient-shift 6s ease infinite;
    letter-spacing: 2px;
    text-shadow: 0px 4px 15px rgba(0, 229, 255, 0.2);
  }

  @keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }

  .header-icon {
    filter: drop-shadow(0 0 12px currentColor);
    animation: float-icon 3s ease-in-out infinite;
  }

  .header-icon:nth-child(3) {
    animation-delay: 1.5s;
  }

  @keyframes float-icon {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }

  .glass-chip {
    background: rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
  }

  .header-glow {
    position: absolute;
    top: 40%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 70%;
    height: 120px;
    background: radial-gradient(circle, rgba(0, 229, 255, 0.15) 0%, rgba(124, 77, 255, 0.05) 40%, rgba(0, 0, 0, 0) 70%);
    z-index: -1;
    pointer-events: none;
  }
  </style>