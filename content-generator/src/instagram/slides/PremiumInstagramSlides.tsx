import React from "react";
import { AlertTriangle, ArrowDownRight, ArrowUpRight, Bookmark, Eye, Flame, Gauge, Send, ShieldAlert, UserPlus } from "lucide-react";
import type { InstagramAnalyticsData } from "../api/types";
import { deriveInstagramStory, getGrowth, getZip } from "../data/deriveInstagramStory";
import { theme } from "../../theme/theme";
import { formatCurrency, formatNumber, formatPercent } from "../../utils/format";
import { AreaTrendChart, Sparkline } from "../components/ChartComponents";
import { CarouselSlide, slideIn, useCountUp } from "../components/CarouselSlide";
import { InsightCard } from "../components/InsightCard";
import { KpiChip, MetricCard, formatMetric } from "../components/MetricCard";
import { RankingCard } from "../components/RankingCard";

const unavailable = "No API data";

const SwipeCue = ({ children, tone = "primary" }: { children: React.ReactNode; tone?: "primary" | "secondary" | "warning" }) => {
  const color = tone === "secondary" ? theme.colors.secondary : tone === "warning" ? theme.colors.warning : theme.colors.primary;
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 12,
        padding: "13px 18px",
        borderRadius: 999,
        background: `${color}14`,
        border: `1px solid ${color}55`,
        color: theme.colors.text,
        fontSize: 21,
        fontWeight: 950,
        marginTop: 28
      }}
    >
      <span style={{ color }}>Swipe</span>
      {children}
    </div>
  );
};

export const LoadingStateSlide = () => (
  <CarouselSlide index={1} section="Loading">
    <div style={{ height: "100%", display: "grid", placeItems: "center", textAlign: "center" }}>
      <div>
        <div style={{ color: theme.colors.primary, fontSize: 34, fontWeight: 950 }}>Fetching Zillow analytics</div>
        <div style={{ color: theme.colors.muted, fontSize: 25, fontWeight: 800, marginTop: 18 }}>
          Building today&apos;s Instagram carousel.
        </div>
      </div>
    </div>
  </CarouselSlide>
);

export const ErrorStateSlide = ({ error }: { error: string }) => (
  <CarouselSlide index={1} section="API error" accent="warning">
    <div style={{ height: "100%", display: "grid", placeItems: "center" }}>
      <div
        style={{
          padding: 42,
          borderRadius: 24,
          background: "rgba(21,27,36,0.84)",
          border: `1px solid ${theme.colors.warning}88`,
          maxWidth: 850
        }}
      >
        <AlertTriangle size={58} color={theme.colors.warning} />
        <h1 style={{ fontSize: 64, lineHeight: 0.98, margin: "28px 0 0", fontWeight: 950 }}>Analytics feed unavailable.</h1>
        <p style={{ color: theme.colors.muted, fontSize: 28, lineHeight: 1.25, fontWeight: 800 }}>{error}</p>
      </div>
    </div>
  </CarouselSlide>
);

export const Slide1Curiosity = ({ data }: { data: InstagramAnalyticsData }) => {
  const story = deriveInstagramStory(data);
  const rent = useCountUp(story.rentDelta, 8);
  return (
    <CarouselSlide index={1} section="Curiosity">
      <div style={{ height: "100%", display: "grid", placeItems: "center", textAlign: "center" }}>
        <div>
          <div style={{ ...slideIn(4), fontSize: 218, lineHeight: 0.8, fontWeight: 950, color: theme.colors.primary }}>
            {formatMetric(rent, "percent")}
          </div>
          <h1 style={{ ...slideIn(12), fontSize: 76, lineHeight: 0.95, margin: "46px 0 0", fontWeight: 950 }}>
            This rent jump is the bait.
          </h1>
          <div style={{ color: theme.colors.muted, fontSize: 32, lineHeight: 1.18, fontWeight: 850, marginTop: 28 }}>
            The real story is hiding one layer deeper.
          </div>
          <div style={{ ...slideIn(18), marginTop: 30 }}>
            <KpiChip label="Market" value={story.marketLabel} />
          </div>
          <SwipeCue>to see the signal behind it.</SwipeCue>
        </div>
      </div>
    </CarouselSlide>
  );
};

export const Slide2Gap = ({ data }: { data: InstagramAnalyticsData }) => {
  const story = deriveInstagramStory(data);
  return (
    <CarouselSlide index={2} section="Information gap" accent="secondary">
      <div style={{ height: "100%", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 28, alignItems: "center" }}>
        <div style={slideIn(4)}>
          <h1 style={{ fontSize: 78, lineHeight: 0.95, margin: 0, fontWeight: 950 }}>Rent is reacting. Supply moved first.</h1>
          <div style={{ color: theme.colors.muted, fontSize: 30, lineHeight: 1.22, fontWeight: 850, marginTop: 34 }}>
            When listings tighten while demand stays awake, prices usually follow.
          </div>
          <SwipeCue tone="secondary">for the proof stack.</SwipeCue>
        </div>
        <div style={{ ...slideIn(12), display: "flex", flexDirection: "column", gap: 18 }}>
          <KpiChip label="Inventory" value={formatMetric(story.inventoryDelta, "percent")} tone="warning" />
          <KpiChip label="Listings" value={formatMetric(story.listings, "number")} tone="secondary" />
          <div
            style={{
              padding: 24,
              borderRadius: 22,
              background: "rgba(21,27,36,0.78)",
              border: `1px solid ${theme.colors.border}`
            }}
          >
            <Sparkline values={story.inventoryTrend.values} color={theme.colors.warning} height={150} />
          </div>
        </div>
      </div>
    </CarouselSlide>
  );
};

export const Slide3Evidence = ({ data }: { data: InstagramAnalyticsData }) => {
  const story = deriveInstagramStory(data);
  return (
    <CarouselSlide index={3} section="Evidence">
      <h1 style={{ ...slideIn(4), fontSize: 68, lineHeight: 0.94, margin: "0 0 28px", fontWeight: 950 }}>
        The move is not random.
      </h1>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <MetricCard label="Avg rent" value={story.avgRent} kind="currency" icon={Flame} delay={8} />
        <MetricCard label="Listings" value={story.listings} kind="number" icon={Gauge} tone="secondary" delay={12} />
        <MetricCard label="Inventory change" value={story.inventoryDelta} kind="percent" icon={ArrowDownRight} tone="warning" delay={16} />
        <MetricCard label="Market score" value={story.score} kind="score" icon={ArrowUpRight} delay={20} />
      </div>
      <div style={{ ...slideIn(26), marginTop: 22, height: 340 }}>
        <AreaTrendChart values={story.rentTrend.values} label="Rent trend" />
      </div>
      <SwipeCue>to see where demand is clustering.</SwipeCue>
    </CarouselSlide>
  );
};

export const Slide4Winners = ({ data }: { data: InstagramAnalyticsData }) => {
  const story = deriveInstagramStory(data);
  return (
    <CarouselSlide index={4} section="Winners">
      <h1 style={{ ...slideIn(4), fontSize: 72, lineHeight: 0.94, margin: "0 0 36px", fontWeight: 950 }}>
        Demand is choosing sides.
      </h1>
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {story.winners.slice(0, 4).map((item, index) => (
          <RankingCard key={`${getZip(item)}-${index}`} item={item} rank={index + 1} mode="winner" />
        ))}
        {story.winners.length === 0 ? <InsightCard icon={ShieldAlert} title={unavailable} detail="Top rent growth returned an empty array." tone="warning" /> : null}
      </div>
      <SwipeCue>before you chase the winners.</SwipeCue>
    </CarouselSlide>
  );
};

export const Slide5Losers = ({ data }: { data: InstagramAnalyticsData }) => {
  const story = deriveInstagramStory(data);
  const deepestDrop = story.losers.map(getGrowth).find((value) => value !== null) ?? null;
  return (
    <CarouselSlide index={5} section="Losers" accent="warning">
      <div style={{ display: "grid", gridTemplateRows: "auto 1fr", gap: 28, height: "100%" }}>
        <h1 style={{ ...slideIn(4), fontSize: 72, lineHeight: 0.94, margin: 0, fontWeight: 950 }}>
          Here is the trap.
        </h1>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 0.8fr", gap: 24 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 15 }}>
            {story.losers.slice(0, 4).map((item, index) => (
              <RankingCard key={`${getZip(item)}-${index}`} item={item} rank={index + 1} mode="loser" />
            ))}
            {story.losers.length === 0 ? <InsightCard icon={ShieldAlert} title={unavailable} detail="Biggest drops returned an empty array." tone="warning" /> : null}
          </div>
          <div
            style={{
              ...slideIn(18),
              padding: 30,
              borderRadius: 22,
              background: "linear-gradient(145deg, rgba(255,200,87,0.16), rgba(21,27,36,0.72))",
              border: `1px solid ${theme.colors.warning}77`,
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between"
            }}
          >
            <div>
              <div style={{ color: theme.colors.muted, fontSize: 22, fontWeight: 900, textTransform: "uppercase" }}>Pressure signal</div>
              <div style={{ color: theme.colors.warning, fontSize: 82, lineHeight: 0.95, fontWeight: 950, marginTop: 24 }}>
                {deepestDrop === null ? "No data" : formatPercent(deepestDrop)}
              </div>
              <div style={{ color: theme.colors.text, fontSize: 34, lineHeight: 1.08, fontWeight: 950, marginTop: 28 }}>
                Some ZIPs are cooling inside the same hot market.
              </div>
            </div>
            <div style={{ color: theme.colors.muted, fontSize: 24, lineHeight: 1.2, fontWeight: 850 }}>
              The winners matter. The losers tell you what can break.
            </div>
          </div>
        </div>
        <SwipeCue tone="warning">for why this spread matters.</SwipeCue>
      </div>
    </CarouselSlide>
  );
};

export const Slide6Why = ({ data }: { data: InstagramAnalyticsData }) => {
  const story = deriveInstagramStory(data);
  const sentence =
    story.inventoryDelta !== null && story.newListings !== null
      ? `Inventory moved ${formatPercent(story.inventoryDelta)} while ${formatNumber(story.newListings)} new listings hit the market. That is the leverage shift.`
      : "Supply data is missing, so the pressure signal cannot be confirmed.";
  return (
    <CarouselSlide index={6} section="Why it matters" accent="secondary">
      <div style={{ height: "100%", display: "grid", placeItems: "center" }}>
        <blockquote style={{ ...slideIn(8), fontSize: 74, lineHeight: 1, fontWeight: 950, margin: 0, maxWidth: 900 }}>
          {sentence}
        </blockquote>
        <SwipeCue tone="secondary">to see who gets leverage.</SwipeCue>
      </div>
    </CarouselSlide>
  );
};

export const Slide7Meaning = ({ data }: { data: InstagramAnalyticsData }) => {
  const story = deriveInstagramStory(data);
  return (
    <CarouselSlide index={7} section="Meaning">
      <h1 style={{ ...slideIn(4), fontSize: 70, lineHeight: 0.94, margin: "0 0 32px", fontWeight: 950 }}>
        Leverage is changing hands.
      </h1>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 22 }}>
        <InsightCard
          icon={ArrowUpRight}
          title="Landlords"
          detail={`Demand score: ${formatMetric(story.demandScore, "score")}. Stronger application flow when supply tightens.`}
          delay={10}
        />
        <InsightCard
          icon={ArrowDownRight}
          title="Renters"
          detail={`Competition score: ${formatMetric(story.competitionScore, "score")}. Less leverage if listings keep falling.`}
          tone="warning"
          delay={16}
        />
      </div>
      <div style={{ ...slideIn(24), marginTop: 24 }}>
        <AreaTrendChart values={story.priceTrend.values} label="Price movement" color={theme.colors.secondary} />
      </div>
      <SwipeCue>for the risk nobody wants to price.</SwipeCue>
    </CarouselSlide>
  );
};

export const Slide8Risk = ({ data }: { data: InstagramAnalyticsData }) => {
  const story = deriveInstagramStory(data);
  const risk =
    story.avgRent !== null && story.medianHomeValue !== null
      ? `${formatCurrency(story.avgRent)} rent against ${formatCurrency(story.medianHomeValue, true)} homes creates affordability pressure.`
      : "Affordability risk cannot be priced without rent and home value data.";
  return (
    <CarouselSlide index={8} section="Risk" accent="warning">
      <div style={{ height: "100%", display: "grid", placeItems: "center" }}>
        <div
          style={{
            ...slideIn(8),
            padding: 42,
            borderRadius: 30,
            background: "linear-gradient(135deg, rgba(255,200,87,0.18), rgba(21,27,36,0.78))",
            border: `1px solid ${theme.colors.warning}88`
          }}
        >
          <AlertTriangle size={70} color={theme.colors.warning} />
          <h1 style={{ fontSize: 78, lineHeight: 0.96, margin: "32px 0 0", fontWeight: 950 }}>The ceiling is affordability.</h1>
          <div style={{ color: theme.colors.muted, fontSize: 32, lineHeight: 1.2, fontWeight: 850, marginTop: 26 }}>{risk}</div>
          <SwipeCue tone="warning">for what happens next.</SwipeCue>
        </div>
      </div>
    </CarouselSlide>
  );
};

export const Slide9Prediction = ({ data }: { data: InstagramAnalyticsData }) => {
  const story = deriveInstagramStory(data);
  const prediction =
    story.inventoryDelta !== null && story.rentDelta !== null
      ? story.inventoryDelta < 0 && story.rentDelta > 0
        ? "If supply stays negative, rent pressure likely continues."
        : "If supply rebounds, rent growth may cool first."
      : "Prediction needs both rent and inventory trend data.";
  return (
    <CarouselSlide index={9} section="Prediction" accent="secondary">
      <div style={{ display: "grid", gridTemplateRows: "auto 1fr", gap: 30, height: "100%" }}>
        <h1 style={{ ...slideIn(4), fontSize: 78, lineHeight: 0.94, margin: 0, fontWeight: 950 }}>The next print decides.</h1>
        <div style={{ display: "grid", gridTemplateColumns: "0.9fr 1.1fr", gap: 26, alignItems: "center" }}>
          <div style={{ ...slideIn(12), display: "flex", flexDirection: "column", gap: 18 }}>
            <KpiChip label="Rent" value={formatMetric(story.rentDelta, "percent")} />
            <KpiChip label="Inventory" value={formatMetric(story.inventoryDelta, "percent")} tone="warning" />
            <KpiChip label="Pulse" value={formatMetric(data.marketPulse?.rent_change_pct, "percent")} tone="secondary" />
          </div>
          <InsightCard icon={Eye} title={prediction} detail="The next inventory print matters more than the last rent headline." tone="secondary" delay={18} />
        </div>
        <SwipeCue tone="secondary">for the daily watchlist.</SwipeCue>
      </div>
    </CarouselSlide>
  );
};

export const Slide10Cta = ({ data }: { data: InstagramAnalyticsData }) => {
  const story = deriveInstagramStory(data);
  return (
    <CarouselSlide index={10} section="Follow CTA">
      <div style={{ height: "100%", display: "grid", gridTemplateColumns: "1fr 0.85fr", gap: 30, alignItems: "center" }}>
        <div style={slideIn(4)}>
          <h1 style={{ fontSize: 78, lineHeight: 0.94, margin: 0, fontWeight: 950 }}>Want the next ZIP before it moves?</h1>
          <div style={{ color: theme.colors.muted, fontSize: 31, lineHeight: 1.22, fontWeight: 850, marginTop: 28 }}>
            Follow for the daily signal: rent pressure, supply shifts, winners, risks.
          </div>
          <div style={{ marginTop: 30 }}>
            <KpiChip label="Today" value={story.marketLabel} />
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {[
            { icon: Bookmark, text: "Save this market." },
            { icon: Send, text: "Share with a friend." },
            { icon: UserPlus, text: "Follow for tomorrow." }
          ].map(({ icon: Icon, text }, index) => (
            <div
              key={text}
              style={{
                ...slideIn(12 + index * 6),
                display: "flex",
                alignItems: "center",
                gap: 16,
                padding: 24,
                borderRadius: 18,
                background: "rgba(21,27,36,0.82)",
                border: `1px solid ${theme.colors.border}`,
                fontSize: 27,
                fontWeight: 950
              }}
            >
              <Icon size={34} color={index === 2 ? theme.colors.primary : theme.colors.secondary} />
              {text}
            </div>
          ))}
        </div>
      </div>
    </CarouselSlide>
  );
};
