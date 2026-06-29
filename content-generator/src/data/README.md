# Data Injection Boundary

`ZillowCarousel` accepts:

```ts
{
  market: ZillowMarketData
}
```

The current `getMockZillowMarket()` provider simulates backend data. A Django serializer can later emit the same JSON shape and pass it to Remotion as `inputProps` without changing slide components.

Required slide count is enforced in `src/ZillowCarousel.tsx` through the ten-item `slideComponents` array.
