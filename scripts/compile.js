import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { scrapeNews } from './scrape-news.js';
import { scrapeMetrics } from './scrape-metrics.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  console.log('[Neuron Pipeline] Starting compilation sequence...');
  const publicDataDir = path.join(__dirname, '../public/data');
  
  // Ensure output directory exists
  if (!fs.existsSync(publicDataDir)) {
    fs.mkdirSync(publicDataDir, { recursive: true });
  }

  try {
    // 1. Run Scrapers
    const news = await scrapeNews();
    const { gridStatus, energyMix } = await scrapeMetrics();

    // 2. Write Output Files
    fs.writeFileSync(path.join(publicDataDir, 'news.json'), JSON.stringify(news, null, 2));
    console.log('[Neuron Pipeline] Wrote news.json');

    fs.writeFileSync(path.join(publicDataDir, 'grid-status.json'), JSON.stringify(gridStatus, null, 2));
    console.log('[Neuron Pipeline] Wrote grid-status.json');

    fs.writeFileSync(path.join(publicDataDir, 'energy-mix.json'), JSON.stringify(energyMix, null, 2));
    console.log('[Neuron Pipeline] Wrote energy-mix.json');

    console.log('[Neuron Pipeline] Compilation finished successfully!');
  } catch (err) {
    console.error('[Neuron Pipeline] Compilation failed:', err);
    process.exit(1);
  }
}

main();
