// JSON-LD schema builders for SEO rich results.
// All schemas follow schema.org and Google's structured data guidelines.
import { siteConfig } from "../../site.config";

const SITE = siteConfig.url;

export function organizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": `${SITE}/#organization`,
    name: siteConfig.name,
    url: SITE,
    logo: `${SITE}/favicon.svg`,
    description:
      "Independent European nutrition decoder. Grades every food and supplement A to E using Open Food Facts, Nutri-Score, NOVA, and the EFSA additives registry. Free, transparent, no brand sponsorship.",
    sameAs: [],
    foundingDate: "2026",
  };
}

export function websiteSchema(locale: "en" | "fr") {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": `${SITE}/#website`,
    url: SITE,
    name: siteConfig.name,
    description:
      locale === "fr"
        ? "Le décodeur d'étiquettes indépendant. Notation A à E basée sur Open Food Facts, Nutri-Score, NOVA et la base EFSA des additifs."
        : "The independent food label decoder. A to E grading based on Open Food Facts, Nutri-Score, NOVA, and the EFSA additives registry.",
    inLanguage: locale === "fr" ? "fr-FR" : "en-US",
    publisher: { "@id": `${SITE}/#organization` },
  };
}

export function breadcrumbSchema(items: { name: string; url?: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, idx) => ({
      "@type": "ListItem",
      position: idx + 1,
      name: item.name,
      ...(item.url ? { item: item.url } : {}),
    })),
  };
}

export function itemListSchema(name: string, urls: string[]) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name,
    numberOfItems: urls.length,
    itemListElement: urls.map((url, idx) => ({
      "@type": "ListItem",
      position: idx + 1,
      url,
    })),
  };
}
