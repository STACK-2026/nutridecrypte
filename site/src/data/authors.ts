// ============================================
// AUTHORS , NutriDécrypte editorial pen names
// Bilingual EN + FR bios, disclosed on /about
// ============================================

export interface AuthorBio {
  en: string;
  fr: string;
}

export interface AuthorData {
  slug: string;
  name: string;
  role: { en: string; fr: string };
  short: AuthorBio;
  long: AuthorBio;
  experience: { en: string; fr: string };
  specialities: { en: string[]; fr: string[] };
  initials: string;
  avatarBg: string;
}

export const AUTHORS: AuthorData[] = [
  {
    slug: "lucie-bernard",
    name: "Lucie Bernard",
    role: {
      en: "Editorial Lead, Food Labelling",
      fr: "Responsable éditoriale, étiquetage alimentaire",
    },
    short: {
      en: "Editorial lead at NutriDécrypte. Eight years covering the European food labelling system, misleading nutrition claims, and consumer-facing health writing.",
      fr: "Responsable éditoriale de NutriDécrypte. Huit ans de couverture du système européen d'étiquetage alimentaire, des allégations nutritionnelles trompeuses et de la santé grand public.",
    },
    long: {
      en: "Lucie Bernard leads editorial at NutriDécrypte. She has eight years of experience covering European food labelling regulation (INCO, FIC), misleading nutrition claims, and consumer nutrition reporting for French and Belgian outlets. She holds a Master in Nutrition and Food Policy from AgroParisTech and focuses on turning ANSES and EFSA opinions into plain, decision-ready guides.",
      fr: "Lucie Bernard dirige l'éditorial de NutriDécrypte. Huit ans à couvrir la réglementation européenne de l'étiquetage (INCO, FIC), les allégations nutritionnelles trompeuses et l'actualité nutrition grand public pour des médias FR et belges. Master en politique nutritionnelle et alimentaire (AgroParisTech). Sa mission : transformer les avis ANSES et EFSA en guides clairs, utilisables au rayon.",
    },
    experience: {
      en: "8 years in food nutrition journalism",
      fr: "8 ans en journalisme nutrition",
    },
    specialities: {
      en: ["Food labelling (INCO/FIC)", "Nutri-Score analysis", "Claims audit", "Consumer reporting"],
      fr: ["Étiquetage (INCO/FIC)", "Analyse Nutri-Score", "Audit allégations", "Enquêtes conso"],
    },
    initials: "LB",
    avatarBg: "linear-gradient(135deg, #0f766e, #065f46)",
  },
  {
    slug: "camille-roux",
    name: "Camille Roux",
    role: {
      en: "Data Analyst, Food Science",
      fr: "Analyste données, sciences alimentaires",
    },
    short: {
      en: "Food science data analyst focused on Open Food Facts, the EFSA additives registry, and the NOVA ultra-processing classification.",
      fr: "Analyste data en sciences alimentaires, spécialiste d'Open Food Facts, de la base EFSA des additifs et de la classification NOVA.",
    },
    long: {
      en: "Camille Roux runs the data side of NutriDécrypte. She pulls and cross-references Open Food Facts, the EFSA additives database, and the NOVA classification of ultra-processed foods to build the NutriDécrypte Score algorithm. Seven years of consumer research and a MSc in Food Science from the University of Ghent. On NutriDécrypte she owns the reproducibility of every grade.",
      fr: "Camille Roux dirige la partie data de NutriDécrypte. Elle tire et croise Open Food Facts, la base EFSA des additifs et la classification NOVA des ultra-transformés pour bâtir l'algorithme NutriDécrypte Score. Sept ans de consumer research, MSc en sciences alimentaires (Université de Gand). Sur NutriDécrypte elle garantit la reproductibilité de chaque note.",
    },
    experience: {
      en: "7 years consumer food data",
      fr: "7 ans de data agro-conso",
    },
    specialities: {
      en: ["Open Food Facts", "EFSA additives", "NOVA classification", "Reproducible scoring"],
      fr: ["Open Food Facts", "Additifs EFSA", "Classification NOVA", "Scoring reproductible"],
    },
    initials: "CR",
    avatarBg: "linear-gradient(135deg, #f59e0b, #b45309)",
  },
  {
    slug: "thomas-moreau",
    name: "Thomas Moreau",
    role: {
      en: "Investigative Food Journalist",
      fr: "Journaliste investigation agroalimentaire",
    },
    short: {
      en: "Investigative journalist tracking the marketing of ultra-processed foods, supplement brands, and the gap between front-of-pack claims and the real ingredient list.",
      fr: "Journaliste investigation qui traque le marketing des ultra-transformés, les marques de compléments et l'écart entre le recto du paquet et la vraie liste d'ingrédients.",
    },
    long: {
      en: "Thomas Moreau covers the marketing side of the food industry for NutriDécrypte. His beat: ultra-processed food launches, supplement brands, and the gap between 'natural' front-of-pack promises and what shows up in the ingredient list. Six years at consumer magazines in France and Switzerland, degree in journalism from CELSA Paris.",
      fr: "Thomas Moreau couvre le marketing de l'agroalimentaire pour NutriDécrypte. Son terrain : lancements d'ultra-transformés, marques de compléments, écart entre les promesses 'naturel' du recto et la vraie liste d'ingrédients. Six ans en magazines conso FR et suisses, CELSA Paris.",
    },
    experience: {
      en: "6 years food industry investigations",
      fr: "6 ans d'investigations agro",
    },
    specialities: {
      en: ["Ultra-processed food", "Supplement marketing", "Misleading claims", "Brand strategy"],
      fr: ["Ultra-transformés", "Marketing compléments", "Allégations trompeuses", "Stratégie de marque"],
    },
    initials: "TM",
    avatarBg: "linear-gradient(135deg, #8b5cf6, #6d28d9)",
  },
  {
    slug: "sarah-keller",
    name: "Sarah Keller",
    role: {
      en: "Registered Dietitian",
      fr: "Diététicienne-nutritionniste",
    },
    short: {
      en: "Registered dietitian (FSHN) reviewing NutriDécrypte guides on supplements, deficiencies, and specific diets (vegan, low-FODMAP, diabetes-friendly).",
      fr: "Diététicienne-nutritionniste diplômée (FSHN) qui relit les guides NutriDécrypte sur les compléments, les carences et les régimes spécifiques (végane, low-FODMAP, diabète).",
    },
    long: {
      en: "Sarah Keller is a registered dietitian based in Geneva with clinical practice experience in both Switzerland and France. She reviews NutriDécrypte editorial content for guides on supplements, vitamin deficiencies, and specific diets (vegan, low-FODMAP, diabetes-friendly). She is the clinical reviewer for content flagged with lastReviewed and reviewedBy tags.",
      fr: "Sarah Keller est diététicienne-nutritionniste basée à Genève, expérience clinique en Suisse et en France. Elle relit le contenu éditorial de NutriDécrypte sur les compléments, les carences vitaminiques et les régimes spécifiques (végane, low-FODMAP, diabète). C'est elle qui signe les relectures cliniques (lastReviewed, reviewedBy).",
    },
    experience: {
      en: "10 years clinical nutrition practice",
      fr: "10 ans de pratique clinique",
    },
    specialities: {
      en: ["Supplement safety", "Micronutrient deficiencies", "Special diets", "Clinical review"],
      fr: ["Sécurité compléments", "Carences micronutriments", "Régimes spécifiques", "Relecture clinique"],
    },
    initials: "SK",
    avatarBg: "linear-gradient(135deg, #0ea5e9, #0369a1)",
  },
];

export const DEFAULT_REVIEWER_NOTE = {
  en: "Reviewed against ANSES, EFSA, and published nutrition science. NutriDécrypte is an independent editorial rating service, not a medical practice.",
  fr: "Relu contre les avis ANSES, EFSA et la littérature nutritionnelle publiée. NutriDécrypte est un service éditorial de notation indépendant, pas un cabinet médical.",
};

export function getAuthorBySlug(slug: string): AuthorData | undefined {
  return AUTHORS.find((a) => a.slug === slug);
}

export function authorForIndex(index: number): AuthorData {
  return AUTHORS[index % AUTHORS.length];
}
