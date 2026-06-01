import { siteConfig, fullUrl } from "./config";

interface MetaProps {
  title: string;
  description: string;
  url: string;
  image?: string;
  type?: "website" | "article";
  publishedTime?: string;
  modifiedTime?: string;
  author?: string;
  keywords?: string[];
}

/** Generate meta tags array for <head> */
export function generateMeta(props: MetaProps) {
  const image = props.image || siteConfig.ogImage;
  const imageUrl = image.startsWith("http") ? image : fullUrl(image);

  return {
    title: props.title,
    description: props.description,
    canonical: props.url,
    og: {
      title: props.title,
      description: props.description,
      url: props.url,
      image: imageUrl,
      type: props.type || "website",
      locale: siteConfig.locale,
      siteName: siteConfig.name,
      ...(props.publishedTime && {
        "article:published_time": props.publishedTime,
      }),
      ...(props.modifiedTime && {
        "article:modified_time": props.modifiedTime,
      }),
    },
    twitter: {
      card: "summary_large_image",
      title: props.title,
      description: props.description,
      image: imageUrl,
      site: siteConfig.twitterHandle,
    },
  };
}

/** JSON-LD for Organization + WebSite (homepage) */
export function jsonLdHomepage() {
  return [
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      name: siteConfig.name,
      url: siteConfig.url,
      description: siteConfig.description,
      ...(siteConfig.legal.email && {
        contactPoint: {
          "@type": "ContactPoint",
          email: siteConfig.legal.email,
          contactType: "customer service",
          availableLanguage: "French",
        },
      }),
    },
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      name: siteConfig.name,
      url: siteConfig.url,
      description: siteConfig.tagline,
      inLanguage: siteConfig.locale,
      potentialAction: {
        "@type": "SearchAction",
        target: {
          "@type": "EntryPoint",
          urlTemplate: `${siteConfig.url}/blog?q={search_term_string}`,
        },
        "query-input": "required name=search_term_string",
      },
    },
  ];
}

/** JSON-LD for Article */
export function jsonLdArticle(article: {
  title: string;
  description: string;
  url: string;
  datePublished: string;
  dateModified?: string;
  image?: string;
  author?: string;
  keywords?: string[];
}) {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.description,
    url: article.url,
    datePublished: article.datePublished,
    dateModified: article.dateModified || article.datePublished,
    image: article.image
      ? article.image.startsWith("http")
        ? article.image
        : fullUrl(article.image)
      : undefined,
    author: {
      "@type": "Organization",
      name: article.author || siteConfig.blog.defaultAuthor,
      url: siteConfig.url,
    },
    publisher: {
      "@type": "Organization",
      name: siteConfig.name,
      url: siteConfig.url,
    },
    mainEntityOfPage: { "@type": "WebPage", "@id": article.url },
    keywords: article.keywords?.join(", "),
    inLanguage: siteConfig.locale,
    speakable: {
      "@type": "SpeakableSpecification",
      cssSelector: ["h1", "h2", "[data-speakable]"],
    },
  };
}

/** JSON-LD for FAQPage */
export function jsonLdFaq(
  faq: Array<{ question: string; answer: string }>
) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faq.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer,
      },
    })),
  };
}

/** JSON-LD for BreadcrumbList */
export function jsonLdBreadcrumbs(
  items: Array<{ name: string; url: string }>
) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: item.name,
      item: item.url,
    })),
  };
}

/**
 * Build a dynamic, data-derived FAQ for a product page (FR/EN). Every answer
 * restates a real signal from the product record (grade, NOVA group, additives,
 * Nutri-Score) — no fabrication. Returns 3-5 {question, answer} pairs.
 */
export function buildProductFaq(
  p: any,
  locale: "fr" | "en"
): Array<{ question: string; answer: string }> {
  const fr = locale === "fr";
  const name = p.name as string;
  const grade = p.grade || (fr ? "non noté" : "ungraded");
  const score = p.score_overall != null ? `${p.score_overall}/100` : null;
  const nova = p.nova_group ? Number(p.nova_group) : null;
  const nutri = p.nutrition_grade ? String(p.nutrition_grade).toUpperCase() : null;
  const addCount = Array.isArray(p.additives_tags) ? p.additives_tags.length : 0;
  const warnings: string[] = Array.isArray(p.warnings) ? p.warnings : [];
  const out: Array<{ question: string; answer: string }> = [];

  out.push({
    question: fr ? `Quelle note obtient ${name} ?` : `What grade does ${name} get?`,
    answer: fr
      ? `${name} obtient la note ${grade}${score ? ` (${score})` : ""} selon la méthode NutriDécrypte, qui combine le Nutri-Score, le degré d'ultra-transformation NOVA, le risque additifs, les allégations marketing et la densité nutritionnelle, à partir des données Open Food Facts, EFSA et ANSES.`
      : `${name} gets a grade of ${grade}${score ? ` (${score})` : ""} under the NutriDécrypte method, which combines Nutri-Score, NOVA ultra-processing, additive risk, marketing claims and nutritional density, based on Open Food Facts, EFSA and ANSES data.`,
  });

  if (nova) {
    const up = nova >= 4;
    out.push({
      question: fr ? `${name} est-il ultra-transformé ?` : `Is ${name} ultra-processed?`,
      answer: fr
        ? `Son groupe NOVA est ${nova} sur 4. ${up ? "Un groupe NOVA 4 signale un aliment ultra-transformé, à limiter dans l'alimentation quotidienne." : "Plus le groupe NOVA est bas, moins l'aliment est transformé."}`
        : `Its NOVA group is ${nova} of 4. ${up ? "NOVA group 4 flags an ultra-processed food, best limited in a daily diet." : "The lower the NOVA group, the less processed the food."}`,
    });
  }

  out.push({
    question: fr ? `${name} contient-il des additifs ?` : `Does ${name} contain additives?`,
    answer: fr
      ? `${addCount === 0 ? "Aucun additif n'a été détecté" : `${addCount} additif${addCount > 1 ? "s ont" : " a"} été détecté${addCount > 1 ? "s" : ""}`} via Open Food Facts.${warnings.length ? ` Points de vigilance : ${warnings.slice(0, 3).join(", ")}.` : ""}`
      : `${addCount === 0 ? "No additive was detected" : `${addCount} additive${addCount > 1 ? "s were" : " was"} detected`} via Open Food Facts.${warnings.length ? ` Watch-outs: ${warnings.slice(0, 3).join(", ")}.` : ""}`,
  });

  if (nutri) {
    out.push({
      question: fr ? `Quel est le Nutri-Score de ${name} ?` : `What is the Nutri-Score of ${name}?`,
      answer: fr
        ? `Son Nutri-Score est ${nutri} (échelle A à E). Le Nutri-Score résume la qualité nutritionnelle, mais NutriDécrypte le complète avec la transformation et les additifs pour une note plus complète.`
        : `Its Nutri-Score is ${nutri} (A to E scale). Nutri-Score summarises nutritional quality, but NutriDécrypte adds processing and additives for a more complete verdict.`,
    });
  }

  return out;
}

/** Dynamic FAQ for a category hub page (FR/EN). */
export function buildCategoryFaq(
  categoryPretty: string,
  count: number,
  avgScore: number | string | null,
  best: { name?: string; grade?: string } | null,
  locale: "fr" | "en"
): Array<{ question: string; answer: string }> {
  const fr = locale === "fr";
  const cat = categoryPretty.toLowerCase();
  const out: Array<{ question: string; answer: string }> = [
    {
      question: fr ? `Combien de produits ${cat} sont notés ?` : `How many ${cat} products are graded?`,
      answer: fr
        ? `${count} produits ${cat} sont notés de A à E par NutriDécrypte${avgScore != null ? `, avec un score moyen de ${avgScore}/100` : ""}.`
        : `${count} ${cat} products are graded A to E by NutriDécrypte${avgScore != null ? `, with a mean score of ${avgScore}/100` : ""}.`,
    },
    {
      question: fr ? `Comment bien choisir un produit ${cat} ?` : `How to choose a good ${cat} product?`,
      answer: fr
        ? `Privilégiez un bon Nutri-Score (A ou B), un groupe NOVA bas (aliment peu transformé) et une liste d'additifs courte. Le prix et le marketing ne sont pas des indicateurs de qualité.`
        : `Prefer a good Nutri-Score (A or B), a low NOVA group (minimally processed) and a short additives list. Price and marketing are not quality indicators.`,
    },
    {
      question: fr ? `Comment NutriDécrypte calcule-t-il la note ?` : `How does NutriDécrypte compute the grade?`,
      answer: fr
        ? `La note A à E combine cinq axes (Nutri-Score, ultra-transformation NOVA, additifs, allégations et densité nutritionnelle) de façon déterministe, à partir des données Open Food Facts, EFSA et ANSES.`
        : `The A to E grade deterministically combines five axes (Nutri-Score, NOVA ultra-processing, additives, claims and nutritional density), from Open Food Facts, EFSA and ANSES data.`,
    },
  ];
  if (best && best.name) {
    out.splice(1, 0, {
      question: fr ? `Quel est le meilleur produit ${cat} ?` : `What is the best ${cat} product?`,
      answer: fr
        ? `Le mieux noté de notre classement ${cat} est ${best.name}${best.grade ? ` (note ${best.grade})` : ""}.`
        : `The top-rated in our ${cat} ranking is ${best.name}${best.grade ? ` (grade ${best.grade})` : ""}.`,
    });
  }
  return out;
}
