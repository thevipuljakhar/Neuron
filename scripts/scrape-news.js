import Parser from 'rss-parser';

const parser = new Parser({
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  }
});

// Curated RSS feeds for India, US, and Global
const FEEDS = [
  // India (70%)
  { url: 'https://economictimes.indiatimes.com/industry/energy/power/rssfeeds/13358066.cms', region: 'India', source: 'Economic Times' },
  { url: 'https://www.livemint.com/rss/industry', region: 'India', source: 'LiveMint' },
  // US (15%)
  { url: 'https://news.google.com/rss/search?q=us+power+grid+energy+news', region: 'US', source: 'Google News US' },
  // Global (15%)
  { url: 'https://news.google.com/rss/search?q=global+renewable+energy+industry', region: 'Globe', source: 'Google News Global' }
];

const KEYWORDS = [
  'power', 'electricity', 'solar', 'wind', 'coal', 'grid', 'battery', 'generator', 'turbine',
  'nuclear', 'hydro', 'renewables', 'lng', 'gas', 'oil', 'petroleum', 'shortage', 'outage',
  'energy', 'disruption', 'thermal', 'biomass'
];

export async function scrapeNews() {
  console.log('[News Scraper] Starting RSS ingestion...');
  const allArticles = [];

  for (const feed of FEEDS) {
    try {
      console.log(`[News Scraper] Fetching ${feed.source}...`);
      const feedData = await parser.parseURL(feed.url);
      
      for (const item of feedData.items) {
        const title = item.title || '';
        const content = item.contentSnippet || item.content || '';
        const combinedText = (title + ' ' + content).toLowerCase();

        // Check if article is energy related
        const isEnergyRelated = KEYWORDS.some(keyword => combinedText.includes(keyword));
        if (!isEnergyRelated) continue;

        // Determine category
        let category = 'Grid';
        if (combinedText.includes('solar') || combinedText.includes('wind') || combinedText.includes('renew') || combinedText.includes('hydro')) {
          category = 'Renewable';
        } else if (combinedText.includes('coal') || combinedText.includes('oil') || combinedText.includes('gas') || combinedText.includes('thermal') || combinedText.includes('lng')) {
          category = 'Fossil';
        }

        allArticles.push({
          id: `${feed.region.toLowerCase().slice(0,2)}-${Math.random().toString(36).slice(2, 7)}`,
          title: title.trim(),
          summary: content.slice(0, 200).trim() + (content.length > 200 ? '...' : ''),
          source: feed.source,
          timestamp: item.pubDate ? new Date(item.pubDate).toISOString() : new Date().toISOString(),
          region: feed.region,
          category,
          link: item.link || '#'
        });
      }
    } catch (err) {
      console.error(`[News Scraper] Failed to fetch feed ${feed.source}:`, err.message);
    }
  }

  // Separate by region
  const indiaArticles = allArticles.filter(a => a.region === 'India').sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  const usArticles = allArticles.filter(a => a.region === 'US').sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  const globeArticles = allArticles.filter(a => a.region === 'Globe').sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  // Enforce 70:15:15 ratio (target total 20 items: 14 India, 3 US, 3 Globe)
  const finalArticles = [
    ...indiaArticles.slice(0, 14),
    ...usArticles.slice(0, 3),
    ...globeArticles.slice(0, 3)
  ];

  console.log(`[News Scraper] Ingested ${finalArticles.length} normalized energy reports matching target ratio.`);
  return finalArticles;
}
