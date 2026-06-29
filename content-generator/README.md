# Zillow Real Estate Intelligence Carousel

Production-grade Remotion system for generating LinkedIn carousels from Zillow-style real estate analytics data.

## Commands

```bash
npm install
npm run dev
npm run typecheck
npm run still
npm run build
```

The mock provider in `src/data/mockZillow.ts` is shaped to match backend serializer injection later. Pass a `market` prop into `ZillowCarousel` or replace the provider boundary with Django serializer JSON.

## Templates

- `ZillowIntelligenceCarousel`: LinkedIn carousel.
- `InstagramZillowCarousel`: Instagram carousel.

Export Instagram PNGs:

```bash
npm run export:instagram
```
