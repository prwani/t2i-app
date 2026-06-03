"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL, Scenario, api } from "../lib/api";

const generationModels = ["MAI-Image-2e", "MAI-Image-2.5-Flash", "MAI-Image-2.5", "MAI-Image-2", "gpt-image-2"];

const fallbackScenarios: Scenario[] = [
  {
    id: "product-launch",
    name: "Product launch",
    description: "Hero visuals, launch banners, and social-ready concepts for a new product.",
    defaultModel: "MAI-Image-2e",
    modelOptions: generationModels,
    defaultPrompt: "Create a premium product launch hero image for a sleek smart speaker on a warm gradient studio background.",
    examples: [],
    exampleExtras: []
  },
  {
    id: "seasonal-campaign",
    name: "Seasonal campaign",
    description: "High-converting campaign artwork for holidays, promos, and limited runs.",
    defaultModel: "MAI-Image-2e",
    modelOptions: generationModels,
    defaultPrompt: "Design a festive but modern winter campaign image for a coffee brand, cozy lighting, premium packaging.",
    examples: [],
    exampleExtras: []
  },
  {
    id: "brand-refresh",
    name: "Brand refresh",
    description: "Explore new visual systems while preserving brand cues and audience fit.",
    defaultModel: "MAI-Image-2e",
    modelOptions: generationModels,
    defaultPrompt: "Create three visual directions for a modern wellness brand refresh using calming gradients and natural textures.",
    examples: [],
    exampleExtras: []
  }
];

const evalUtils = [
  { id: "evaluate", name: "Evaluate", description: "Score a single asset for brand fit, prompt adherence, and conversion potential.", icon: "📊" },
  { id: "compare", name: "Compare", description: "Side-by-side comparison of two or more generated assets.", icon: "⚖️" },
  { id: "batch-rank", name: "Batch Rank", description: "Rank an entire set and surface a recommended winner.", icon: "🏆" }
];

export default function Home() {
  const router = useRouter();
  const [apiOnline, setApiOnline] = useState<"checking" | "online" | "offline">("checking");
  const [scenarios, setScenarios] = useState<Scenario[]>(fallbackScenarios);

  useEffect(() => {
    let ignore = false;
    async function bootstrap() {
      try {
        await api.health();
        if (!ignore) setApiOnline("online");
      } catch {
        if (!ignore) setApiOnline("offline");
      }
      try {
        const remote = await api.scenarios();
        if (!ignore && remote.length) setScenarios(remote);
      } catch { /* use fallbacks */ }
    }
    bootstrap();
    return () => { ignore = true; };
  }, []);

  return (
    <main className="homePage">
      <nav className="topbar" aria-label="Product">
        <div className="brand">
          <span className="brandMark">AC</span>
          <span>Asset Creation Workflow</span>
        </div>
        <span className={`apiPill ${apiOnline}`}>API {apiOnline}</span>
      </nav>

      <header className="homeHero">
        <p className="eyebrow">Generate · Evaluate · Compare</p>
        <h1>Create campaign-ready assets with AI</h1>
        <p className="heroSub">
          Pick a scenario below, craft your prompt, generate assets, then score and compare outputs — all in one workflow.
        </p>
      </header>

      <div className="homeGrid">
        {/* Left column — scenarios */}
        <section>
          <h2 className="columnHead">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none"><rect x="2" y="2" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.6"/><rect x="11" y="2" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.6"/><rect x="2" y="11" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.6"/><rect x="11" y="11" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.6"/></svg>
            Content Creation Scenarios
          </h2>
          <ul className="linkList">
            {scenarios.map((s) => (
              <li key={s.id}>
                <button type="button" className="linkCard" onClick={() => router.push(`/studio/${encodeURIComponent(s.id)}`)}>
                  <strong>{s.name}</strong>
                  <span>{s.description}</span>
                  <small>{s.defaultModel}</small>
                </button>
              </li>
            ))}
          </ul>
        </section>

        {/* Right column — evaluation utils */}
        <section>
          <h2 className="columnHead">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7.25" stroke="currentColor" strokeWidth="1.6"/><path d="M10 6v4l2.5 2.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Evaluation Utils
          </h2>
          <ul className="linkList">
            {evalUtils.map((u) => (
              <li key={u.id}>
                <button type="button" className="linkCard" onClick={() => router.push(`/studio/product-launch?eval=${u.id}`)}>
                  <strong>
                    <span className="utilIcon">{u.icon}</span>
                    {u.name}
                  </strong>
                  <span>{u.description}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <footer className="homeFooter">
        <span className="endpoint">API: {API_BASE_URL}</span>
      </footer>
    </main>
  );
}
