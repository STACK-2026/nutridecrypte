// ============================================
// i18n dictionary , NutriDécrypte site
// EN + FR bilingual from day 1
// ============================================

export type Locale = "en" | "fr";

export const LOCALES: Locale[] = ["en", "fr"];
export const DEFAULT_LOCALE: Locale = "en";

export interface Translation {
  en: string;
  fr: string;
}

// Utility: pick the right language from a translation object
export function t(tr: Translation, locale: Locale = DEFAULT_LOCALE): string {
  return tr[locale] || tr.en;
}

// Utility: get the URL prefix for a locale (en = "", fr = "/fr")
export function localeUrl(path: string, locale: Locale = DEFAULT_LOCALE): string {
  if (locale === "en") return path;
  if (path === "/") return "/fr/";
  return "/fr" + (path.startsWith("/") ? path : "/" + path);
}

// Utility: detect current locale from Astro URL
export function getLocale(url: URL | string): Locale {
  const pathname = typeof url === "string" ? url : url.pathname;
  if (pathname.startsWith("/fr/") || pathname === "/fr") return "fr";
  return "en";
}

// ============================================
// TRANSLATIONS , bilingual dictionary
// ============================================

export const tr = {
  // Navigation
  nav: {
    home: { en: "Home", fr: "Accueil" },
    rankings: { en: "Catalog", fr: "Catalogue" },
    compare: { en: "Compare", fr: "Comparer" },
    encyclopedia: { en: "Additives", fr: "Additifs" },
    methodology: { en: "Methodology", fr: "Méthodologie" },
    blog: { en: "Blog", fr: "Blog" },
    about: { en: "About", fr: "À propos" },
    score: { en: "Decode a product", fr: "Décrypter un produit" },
    app: { en: "Launch the decoder", fr: "Lancer le décodeur" },
  },

  // Hero
  hero: {
    badge: {
      en: "Independent label decoder",
      fr: "Décodeur d'étiquettes indépendant",
    },
    title1: { en: "We decode what", fr: "On décrypte ce que" },
    title2: { en: "labels hide.", fr: "les étiquettes cachent." },
    lede: {
      en: "Every food and supplement graded A to E. Additives, ultra-processing, misleading claims, Nutri-Score, NOVA. Independent, free, sources ANSES + EFSA + Open Food Facts.",
      fr: "Chaque aliment et complément noté de A à E. Additifs, ultra-transformation, allégations trompeuses, Nutri-Score, NOVA. Indépendant, gratuit, sources ANSES + EFSA + Open Food Facts.",
    },
    searchPlaceholder: {
      en: "Search a brand, product, or paste an ingredient list",
      fr: "Cherche une marque, un produit ou colle une liste d'ingrédients",
    },
    ctaPrimary: { en: "Decode a product", fr: "Décrypter un produit" },
    ctaSecondary: { en: "Explore the catalog", fr: "Explorer le catalogue" },
    liveBadge: {
      en: "Sources ANSES, EFSA, Open Food Facts",
      fr: "Sources ANSES, EFSA, Open Food Facts",
    },
    bullet1: { en: "A to E grading in 5 dimensions", fr: "Notation A à E sur 5 dimensions" },
    bullet2: { en: "EFSA additive risk index", fr: "Indice de risque additifs EFSA" },
    bullet3: { en: "100% free, zero brand paid", fr: "100% gratuit, aucune marque ne paie" },
  },

  // How it works
  how: {
    eyebrow: { en: "How it works", fr: "Comment ça marche" },
    title: {
      en: "Three steps to decode any label",
      fr: "Trois étapes pour décoder n'importe quelle étiquette",
    },
    lede: {
      en: "We combine the Nutri-Score, the NOVA classification, and the EFSA additives registry into a single, reproducible A to E verdict. No marketing spin.",
      fr: "On combine le Nutri-Score, la classification NOVA et la base EFSA des additifs dans un verdict unique A à E, reproductible. Aucun blabla marketing.",
    },
    step1title: { en: "Search the product", fr: "Cherche le produit" },
    step1body: {
      en: "Find a brand, scan a barcode, or paste an ingredient list. The catalog is built from Open Food Facts and covers three million European references.",
      fr: "Trouve une marque, scanne un code-barres ou colle une liste d'ingrédients. Le catalogue est bâti sur Open Food Facts et couvre trois millions de références européennes.",
    },
    step2title: { en: "Read the real verdict", fr: "Lis le vrai verdict" },
    step2body: {
      en: "Every additive, every claim, every nutritional lie is cross-checked against ANSES and EFSA. You see what the front of pack will never show.",
      fr: "Chaque additif, chaque allégation, chaque mensonge nutritionnel est croisé avec les bases ANSES et EFSA. Tu vois ce que le recto du paquet ne montrera jamais.",
    },
    step3title: { en: "Choose better", fr: "Choisis mieux" },
    step3body: {
      en: "Each page suggests better-graded alternatives from the same category. No upsell to a specific brand, just the data sorted by score.",
      fr: "Chaque fiche propose des alternatives mieux notées du même rayon. Zéro pousse-au-crime vers une marque précise, juste la donnée triée par score.",
    },
  },

  // Methodology teaser
  methodo: {
    eyebrow: { en: "Methodology", fr: "Méthodologie" },
    title: {
      en: "Every grade is deterministic and documented",
      fr: "Chaque note est déterministe et documentée",
    },
    body: {
      en: "Same ingredient list, same grade, every time. No human gut feeling, no sponsor influence, no black-box AI. The full algorithm is open source and reproducible from the methodology page.",
      fr: "Même liste d'ingrédients, même note, à chaque fois. Aucun jugement au feeling, aucune influence sponsor, aucune IA black-box. L'algorithme complet est ouvert et reproductible depuis la page méthodologie.",
    },
    cta: { en: "Read the full methodology", fr: "Lire la méthodologie complète" },
    bullet1: {
      en: "5 weighted axes (Nutri-Score, NOVA, additives, claims, density)",
      fr: "5 axes pondérés (Nutri-Score, NOVA, additifs, allégations, densité)",
    },
    bullet2: {
      en: "EFSA + ANSES + Open Food Facts data",
      fr: "Données EFSA + ANSES + Open Food Facts",
    },
    bullet3: {
      en: "Open, auditable, reproducible",
      fr: "Ouvert, auditable, reproductible",
    },
    bullet4: {
      en: "No brand ever pays to change a grade",
      fr: "Aucune marque ne paie pour changer une note",
    },
  },

  // FAQ
  faq: {
    eyebrow: { en: "FAQ", fr: "FAQ" },
    title: {
      en: "Questions we hear every day",
      fr: "Les questions qu'on nous pose tout le temps",
    },
    q1: {
      en: "How does NutriDécrypte grade products?",
      fr: "Comment NutriDécrypte note les produits ?",
    },
    a1: {
      en: "Every product is graded A to E across five weighted axes: official Nutri-Score (25%), NOVA ultra-processing class (25%), additive risk based on the EFSA registry (20%), marketing claims audit (15%), and nutritional density (15%). Ingredients come from Open Food Facts, the grade is deterministic. No brand can pay to move up.",
      fr: "Chaque produit est noté A à E sur cinq axes pondérés : Nutri-Score officiel (25%), classification NOVA d'ultra-transformation (25%), indice de risque additifs selon la base EFSA (20%), audit des allégations marketing (15%) et densité nutritionnelle (15%). Les ingrédients viennent d'Open Food Facts, la note est déterministe. Aucune marque ne peut acheter une meilleure note.",
    },
    q2: {
      en: "How is this different from the official Nutri-Score?",
      fr: "Quelle est la différence avec le Nutri-Score officiel ?",
    },
    a2: {
      en: "The Nutri-Score is a public tool we use as a building block, but it only looks at nutritional composition. It does not penalize ultra-processing, it does not evaluate additives, it ignores misleading claims. Our A to E grade adds those dimensions that the Nutri-Score leaves out but that matter to modern consumers.",
      fr: "Le Nutri-Score est un outil public qu'on utilise comme brique de base, mais il ne regarde que la composition nutritionnelle. Il ne pénalise pas l'ultra-transformation, il n'évalue pas les additifs, il ignore les allégations trompeuses. Notre note A à E intègre ces dimensions que le Nutri-Score laisse de côté et qui comptent pour le consommateur moderne.",
    },
    q3: { en: "Where does your data come from?", fr: "D'où viennent vos données ?" },
    a3: {
      en: "Our catalog is built from Open Food Facts (a collaborative database of three million European products), enriched with the EFSA food additives database, the NOVA classification from the University of São Paulo, and the latest ANSES publications. Sources are cited on every product page and every article.",
      fr: "Notre catalogue est construit à partir d'Open Food Facts (base collaborative de 3 millions de produits européens), enrichi avec la base EFSA des additifs alimentaires, la classification NOVA de l'Université de São Paulo et les dernières publications de l'ANSES. Les sources sont citées sur chaque fiche produit et chaque article.",
    },
    q4: { en: "Is it really free?", fr: "C'est vraiment gratuit ?" },
    a4: {
      en: "Yes. Browsing the grades, comparing products, exploring the additives encyclopedia, and reading the articles is 100% free. NutriDécrypte is funded through affiliate partnerships with brands selected for quality (never by buying a grade) and through an optional premium newsletter down the road.",
      fr: "Oui. Consulter les notes, comparer, parcourir la base additifs et lire les articles est 100% gratuit. NutriDécrypte se finance via des partenariats d'affiliation avec des marques sélectionnées pour leur qualité (jamais par achat de note) et via une newsletter premium optionnelle à terme.",
    },
  },

  // Final CTA
  finalCta: {
    title: {
      en: "Stop trusting the front of pack. Read the real grade.",
      fr: "Arrête de croire le recto du paquet. Lis la vraie note.",
    },
    body: {
      en: "Search any product, compare two labels side by side, paste an ingredient list. The true A to E verdict in under a second.",
      fr: "Cherche un produit, compare deux étiquettes cote à cote, colle une liste d'ingrédients. Le vrai verdict A à E en moins d'une seconde.",
    },
    cta: { en: "Decode a product", fr: "Décrypter un produit" },
    stat1: { en: "additives referenced", fr: "additifs référencés" },
    stat2: { en: "official sources", fr: "sources officielles" },
    stat3: { en: "always free", fr: "toujours gratuit" },
  },

  // Footer
  footer: {
    tagline: {
      en: "Independent food label decoder, A to E",
      fr: "Décodeur d'étiquettes indépendant, de A à E",
    },
    blurb: {
      en: "Every food and supplement graded across 5 axes: Nutri-Score, NOVA, additives, claims, density. Free, transparent, no brand ever pays.",
      fr: "Chaque aliment et complément noté sur 5 axes : Nutri-Score, NOVA, additifs, allégations, densité. Gratuit, transparent, aucune marque ne paie.",
    },
    colProduct: { en: "Product", fr: "Produit" },
    colCompany: { en: "Company", fr: "Société" },
    colLegal: { en: "Legal", fr: "Mentions légales" },
    rankings: { en: "Catalog", fr: "Catalogue" },
    compare: { en: "Compare", fr: "Comparer" },
    encyclopedia: { en: "Additives encyclopedia", fr: "Encyclopédie des additifs" },
    methodology: { en: "Methodology", fr: "Méthodologie" },
    app: { en: "Launch the decoder", fr: "Lancer le décodeur" },
    about: { en: "About", fr: "À propos" },
    blog: { en: "Blog", fr: "Blog" },
    contact: { en: "Contact", fr: "Contact" },
    privacy: { en: "Privacy policy", fr: "Politique de confidentialité" },
    terms: { en: "Terms of use", fr: "Conditions d'utilisation" },
    cookies: { en: "Cookie policy", fr: "Politique de cookies" },
    disclaimer: {
      en: "NutriDécrypte is an independent editorial rating service, not a medical practice. Grades are informational only. For any nutritional condition, always consult a registered dietitian or physician.",
      fr: "NutriDécrypte est un service éditorial de notation indépendant, pas un cabinet médical. Les notes sont informatives. Pour toute condition nutritionnelle, consulte un diététicien diplômé ou ton médecin.",
    },
  },

  // Cookie banner
  cookie: {
    emoji: { en: "Read the label", fr: "Lis l'étiquette" },
    message: {
      en: "We use a minimal set of cookies: essentials keep the site running, analytics help us improve the grading algorithm. No third-party ads, no resale of your data.",
      fr: "On utilise un ensemble minimal de cookies : les essentiels font tourner le site, l'analytics nous aide à améliorer l'algorithme de notation. Pas de pub tierce, pas de revente de tes données.",
    },
    accept: { en: "Accept all", fr: "Tout accepter" },
    essential: { en: "Essential only", fr: "Essentiels uniquement" },
    policy: { en: "Cookie policy", fr: "Politique de cookies" },
  },

  // 404
  notFound: {
    code: { en: "404", fr: "404" },
    title: {
      en: "This page is not on the label",
      fr: "Cette page n'est pas sur l'étiquette",
    },
    body: {
      en: "Like many marketing claims, it promises something that does not really exist. Let's keep the investigation going.",
      fr: "Comme beaucoup d'allégations marketing, elle promet quelque chose qui n'existe pas vraiment. On continue l'enquête.",
    },
    home: { en: "Back to home", fr: "Retour à l'accueil" },
    score: { en: "Decode a product", fr: "Décrypter un produit" },
    popular: { en: "Popular pages", fr: "Pages populaires" },
  },
};
