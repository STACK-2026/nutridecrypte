// ============================================
// SITE CONFIG , nutridecrypte.com
// On décrypte ce que les étiquettes cachent. EN + FR.
// ============================================

export const siteConfig = {
  // Identity
  name: "NutriDécrypte",
  tagline: "On décrypte ce que les étiquettes cachent",
  description:
    "NutriDécrypte note chaque complément et aliment de A à E. Additifs, ultra-transformation, allégations trompeuses, Nutri-Score, NOVA. Indépendant, gratuit, sources officielles (ANSES, EFSA, Open Food Facts).",
  url: "https://nutridecrypte.com",
  appUrl: "https://nutridecrypte.com",
  locale: "en-US",
  language: "en",

  // Bilingue dès le jour 1 (EN par défaut, FR sous /fr/)
  locales: [
    { code: "en", label: "English", path: "/" },
    { code: "fr", label: "Français", path: "/fr/" },
  ],

  // Palette , "décryptage" : vert scientifique + ambre loupe + encre profonde
  colors: {
    primary: "#0f766e", // teal-700 , science, nature, label bio
    secondary: "#065f46", // emerald-800 , profondeur
    accent: "#f59e0b", // amber-500 , loupe, alerte additif
    alert: "#dc2626", // red-600 , verdicts E, alertes
    background: "#fafaf9", // stone-50 , papier étiquette
    text: "#0c0a09", // stone-950 , encre
  },

  // Typographie
  fonts: {
    display: "Plus Jakarta Sans",
    body: "Inter",
  },

  // SEO
  author: "NutriDécrypte Editorial",
  twitterHandle: "",
  ogImage: "/og-default.jpg",
  keywords: [
    "additifs alimentaires",
    "nutri-score",
    "NOVA ultra-transformé",
    "décodeur étiquettes",
    "complément alimentaire",
    "food additives",
    "ultra-processed food",
    "nutrition label decoder",
    "E numbers EFSA",
    "food marketing claims",
  ],

  // GEO (Generative Engine Optimization)
  llmsDescription:
    "NutriDécrypte.com is an independent European nutrition decoder that scores food and dietary supplements from A to E using public data from Open Food Facts, the Nutri-Score, the NOVA ultra-processed classification, and the EFSA additives registry. It flags misleading marketing claims, ultra-processing, questionable additives, and hidden sugars, and publishes transparent, reproducible ingredient-level analysis for thousands of products sold in France and Europe.",

  // Schema.org
  schema: {
    organizationType: "Organization",
  },

  // UI strings (i18n-ready overrides)
  ui: {
    ctaPrimary: "Décrypter un produit",
    ctaSecondary: "Explorer le catalogue",
    ctaHeader: "Décrypter",
    ctaFooterTitle: "Prêt à savoir vraiment ce que vous mangez ?",
  },

  // Navigation
  navLinks: [
    { label: "Catalogue", href: "/rankings" },
    { label: "Comparer", href: "/compare" },
    { label: "Additifs", href: "/encyclopedia" },
    { label: "Méthodologie", href: "/methodology" },
    { label: "Blog", href: "/blog" },
  ],

  // Landing page sections
  sections: {
    hero: true,
    features: true,
    faq: true,
    cta: true,
    testimonials: false,
  },

  // FAQ
  faq: [
    {
      question: "Comment NutriDécrypte note les produits ?",
      answer:
        "Chaque produit reçoit une note de A à E calculée sur cinq axes : Nutri-Score officiel, classification NOVA (ultra-transformation), additifs (base EFSA avec indice de risque), allégations marketing vérifiées, et densité nutritionnelle. L'algorithme est déterministe : mêmes ingrédients, même note, à chaque fois. Aucune marque ne peut acheter sa note.",
    },
    {
      question: "Quelle est la différence avec le Nutri-Score officiel ?",
      answer:
        "Le Nutri-Score est un outil public que nous utilisons comme brique de base, mais il ne regarde que la composition nutritionnelle. Il ne pénalise pas l'ultra-transformation, n'évalue pas les additifs, et ignore les allégations trompeuses. Notre note A à E intègre ces dimensions que le Nutri-Score laisse de côté et qui intéressent le consommateur moderne.",
    },
    {
      question: "D'où viennent vos données ?",
      answer:
        "Notre catalogue est construit à partir d'Open Food Facts (base collaborative de 3 millions de produits), enrichi avec la base EFSA des additifs alimentaires, la classification NOVA de l'Université de São Paulo, et les dernières publications de l'ANSES. Les sources sont citées sur chaque fiche produit et chaque article.",
    },
    {
      question: "Est-ce que c'est gratuit ?",
      answer:
        "Oui. Consulter les notes produits, comparer, parcourir la base additifs et lire les articles est 100% gratuit. NutriDécrypte se finance via des partenariats d'affiliation avec des marques sélectionnées pour leur qualité (jamais achat de note) et via une newsletter premium optionnelle à terme.",
    },
  ],

  // Features
  features: [
    {
      title: "Décodage en 10 secondes",
      description:
        "Cherchez une marque, un produit, un complément. Vous obtenez une note A à E, le détail additif par additif, et les alternatives mieux notées du même rayon.",
      icon: "zap",
    },
    {
      title: "Anti-marketing",
      description:
        "Chaque allégation trompeuse (naturel, sans sucre ajouté, riche en protéines) est confrontée à la réalité de l'étiquette. On montre le fossé entre la promesse et la composition.",
      icon: "shield",
    },
    {
      title: "Méthodologie ouverte",
      description:
        "L'algorithme, la base ingrédients, les pondérations et les sources sont publics. Vous pouvez reproduire n'importe quelle note depuis la page méthodologie.",
      icon: "chart",
    },
  ],

  // Blog
  blog: {
    enabled: true,
    postsPerPage: 12,
    defaultAuthor: "NutriDécrypte Editorial",
    categories: [
      "additifs",
      "ultra-transforme",
      "nutri-score",
      "allegations",
      "complements",
      "enquetes",
      "methodologie",
    ],
    name: "NutriDécrypte Blog",
    slug: "blog",
  },

  // Legal
  legal: {
    companyName: "",
    siret: "",
    address: "France",
    email: "contact@nutridecrypte.com",
    phone: "",
  },
};
