"use client";

import { type ReactNode, useEffect, useMemo, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { API_BASE_URL, Asset, Job, Scenario, api, normalizeAsset, normalizeJob } from "../../../lib/api";

/* ── fallback scenarios (same as home) ────────────────────────── */
const generationModels = ["MAI-Image-2e", "MAI-Image-2.5-Flash", "MAI-Image-2.5", "MAI-Image-2", "gpt-image-2"];

const fallbackScenarios: Scenario[] = [
  { id: "product-launch", name: "Product launch", description: "Hero visuals, launch banners, and social-ready concepts.", defaultModel: "MAI-Image-2e", modelOptions: generationModels, defaultPrompt: "Create a premium product launch hero image for a sleek smart speaker on a warm gradient studio background.", examples: ["Luxury skincare bottle on marble, soft shadows, editorial campaign style", "Outdoor adventure backpack floating over topographic lines, bold retail banner", "Minimal fintech debit card launch visual with glassmorphism and confident blue lighting"], exampleExtras: [] },
  { id: "seasonal-campaign", name: "Seasonal campaign", description: "High-converting campaign artwork for holidays, promos, and limited runs.", defaultModel: "MAI-Image-2e", modelOptions: generationModels, defaultPrompt: "Design a festive but modern winter campaign image for a coffee brand, cozy lighting, premium packaging.", examples: ["Back-to-school laptop bundle with energetic paper-cut shapes", "Summer travel sale poster with sunlit luggage and tropical gradients", "Black Friday electronics campaign, cinematic product wall, dramatic contrast"], exampleExtras: [] },
  { id: "brand-refresh", name: "Brand refresh", description: "Explore new visual systems while preserving brand cues and audience fit.", defaultModel: "MAI-Image-2e", modelOptions: generationModels, defaultPrompt: "Create three visual directions for a modern wellness brand refresh using calming gradients and natural textures.", examples: ["Premium pet food brand refresh with playful typography and natural ingredients", "B2B SaaS homepage illustration style: trustworthy, modern, human", "Boutique hotel visual identity mood image with art deco cues"], exampleExtras: [] }
];

const statusCopy: Record<string, string> = { queued: "Queued", running: "Generating…", succeeded: "Ready", completed: "Ready", failed: "Needs attention" };

type DetailModal = {
  title: string;
  subtitle?: string;
  body: ReactNode;
};

export default function StudioPage() {
  const params = useParams();
  const router = useRouter();
  const scenarioId = typeof params.scenarioId === "string" ? decodeURIComponent(params.scenarioId) : "";

  /* ── data state ─────────────────────────────────────────────── */
  const [scenarios, setScenarios] = useState<Scenario[]>(fallbackScenarios);
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("MAI-Image-2e");
  const [assetCount, setAssetCount] = useState(4);
  const [size, setSize] = useState("1024x1024");
  const [style, setStyle] = useState("Premium editorial");
  const [selectedExample, setSelectedExample] = useState("Custom");
  const [brandColorsText, setBrandColorsText] = useState("");
  const [fontStyle, setFontStyle] = useState("");
  const [tone, setTone] = useState("");
  const [logoDescription, setLogoDescription] = useState("");
  const [textToRender, setTextToRender] = useState("");
  const [selectedFormats, setSelectedFormats] = useState<string[]>(["instagram_square", "linkedin_banner", "desktop_hero"]);
  const [environmentsText, setEnvironmentsText] = useState("");
  const [refinementsText, setRefinementsText] = useState("");
  const [useSampleInputs, setUseSampleInputs] = useState(false);

  const [job, setJob] = useState<Job | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [isImproving, setIsImproving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [notice, setNotice] = useState("");
  const [evaluation, setEvaluation] = useState<Record<string, unknown> | null>(null);
  const [comparison, setComparison] = useState<Record<string, unknown> | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);
  const [detailModal, setDetailModal] = useState<DetailModal | null>(null);
  const [scenarioPickerOpen, setScenarioPickerOpen] = useState(false);

  const scenario = useMemo(
    () => scenarios.find((s) => s.id === scenarioId) ?? scenarios[0],
    [scenarios, scenarioId]
  );
  const selectedExampleIndex = selectedExample === "Custom" ? -1 : Number.parseInt(selectedExample, 10);
  const selectedExtra = useMemo<Record<string, unknown>>(() => {
    if (!scenario || selectedExampleIndex < 0) return {};
    return scenario.exampleExtras[selectedExampleIndex] ?? {};
  }, [scenario, selectedExampleIndex]);

  /* ── bootstrap ──────────────────────────────────────────────── */
  useEffect(() => {
    let ignore = false;
    async function load() {
      try {
        const remote = await api.scenarios();
        if (!ignore && remote.length) setScenarios(remote);
      } catch { /* use fallbacks */ }
    }
    load();
    return () => { ignore = true; };
  }, []);

  useEffect(() => {
    if (!scenario) return;
    setPrompt(scenario.defaultPrompt);
    setModel(scenario.forcedModel ?? scenario.defaultModel);
    setSelectedExample("Custom");
    setBrandColorsText("");
    setFontStyle("");
    setTone("");
    setLogoDescription("");
    setTextToRender("");
    setSelectedFormats(["instagram_square", "linkedin_banner", "desktop_hero"]);
    setEnvironmentsText("");
    setRefinementsText("");
    setUseSampleInputs(false);
  }, [scenario]);

  useEffect(() => {
    if (selectedExampleIndex < 0 || !scenario) return;
    const extra = scenario.exampleExtras[selectedExampleIndex] ?? {};
    setBrandColorsText(readString(extra.colors));
    setFontStyle(readString(extra.font_style));
    setTone(readString(extra.tone));
    setLogoDescription(readString(extra.logo_description));
    setTextToRender(readString(extra.text));
    setSelectedFormats(readStringArray(extra.formats, ["instagram_square", "linkedin_banner", "desktop_hero"]));
    setEnvironmentsText(readStringArray(extra.environments).join("\n"));
    setRefinementsText(readStringArray(extra.refinements).join("\n"));
    const hasSampleImages = readStringArray(extra.sample_images).length > 0;
    setUseSampleInputs(hasSampleImages);
  }, [scenario, selectedExampleIndex]);

  /* ── poll running job ───────────────────────────────────────── */
  useEffect(() => {
    if (!job || !["queued", "running"].includes(job.status)) return;
    const ctrl = new AbortController();
    const interval = window.setInterval(async () => {
      try {
        const payload = await api.getGeneration(job.id, ctrl.signal);
        const next = normalizeJob(payload);
        setJob(next);
        if (next.assets.length) setAssets(next.assets);
        if (["succeeded", "completed", "failed"].includes(next.status)) {
          window.clearInterval(interval);
          setIsGenerating(false);
        }
      } catch (err) {
        if (!ctrl.signal.aborted) setNotice(err instanceof Error ? err.message : "Unable to refresh job status.");
      }
    }, 2200);
    return () => { ctrl.abort(); window.clearInterval(interval); };
  }, [job]);

  /* ── actions ────────────────────────────────────────────────── */
  const improvePrompt = useCallback(async () => {
    setIsImproving(true);
    setNotice("");
    try {
      const result = await api.improvePrompt({ prompt, scenario: scenario.id });
      setPrompt(result.improved_prompt ?? result.prompt ?? prompt);
      if (result.suggestions?.length) setNotice(result.suggestions.join(" "));
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Prompt improvement unavailable.");
    } finally {
      setIsImproving(false);
    }
  }, [prompt, scenario]);

  const generateAssets = useCallback(async () => {
    setIsGenerating(true);
    setNotice("");
    setEvaluation(null);
    setComparison(null);
    try {
      const payload: Record<string, unknown> = {
        scenario: scenario.id,
        prompt,
        model: scenario.forcedModel ?? model,
        n: Math.min(Math.max(assetCount, 1), 4),
        size,
        quality: "high"
      };

      if (scenario.id === "brand-template") {
        payload.brand_colors = splitCsv(brandColorsText);
        payload.font_style = fontStyle;
        payload.tone = tone;
        payload.logo_description = logoDescription || undefined;
      }
      if (scenario.id === "text-rendering") {
        payload.text = textToRender;
      }
      if (scenario.id === "aspect-ratio-package") {
        payload.formats = selectedFormats;
      }
      if (scenario.id === "product-placement") {
        payload.environments = splitLines(environmentsText);
      }
      if (scenario.id === "multi-turn-refinement") {
        payload.refinements = splitLines(refinementsText);
      }

      const sampleImagePaths = readStringArray(selectedExtra.sample_images);
      if (useSampleInputs && sampleImagePaths.length) {
        payload.source_images = await Promise.all(sampleImagePaths.map((path) => samplePathToAssetInput(path)));
      }
      const sampleMaskPath = readString(selectedExtra.sample_images_mask);
      if (useSampleInputs && sampleMaskPath) {
        payload.mask = await samplePathToAssetInput(sampleMaskPath);
      }

      if (scenario.id === "multi-image-composition" && (!Array.isArray(payload.source_images) || payload.source_images.length < 2)) {
        throw new Error("Select an example with sample input images for multi-image composition.");
      }
      if (scenario.id === "inpainting" && (!Array.isArray(payload.source_images) || payload.source_images.length !== 1)) {
        throw new Error("Select an example with source and mask sample images for inpainting.");
      }
      if (scenario.id === "product-placement" && (!Array.isArray(payload.source_images) || payload.source_images.length !== 1)) {
        throw new Error("Select an example with a sample product image for product placement.");
      }

      const result = await api.createGeneration(payload);
      const next = normalizeJob(result);
      setJob(next);
      if (next.assets.length) setAssets(next.assets);
      if (!["queued", "running"].includes(next.status)) setIsGenerating(false);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Generation request failed.");
      setIsGenerating(false);
    }
  }, [
    scenario,
    prompt,
    model,
    assetCount,
    size,
    brandColorsText,
    fontStyle,
    tone,
    logoDescription,
    textToRender,
    selectedFormats,
    environmentsText,
    refinementsText,
    selectedExtra,
    useSampleInputs,
  ]);

  const runEvaluation = useCallback(async (mode: "evaluate" | "compare" | "batch-rank") => {
    if (!assets.length) { setNotice("Generate assets first."); return; }
    setIsEvaluating(true);
    setNotice("");
    try {
      const body = { prompt, assets: assets.map((a) => ({ id: a.id, name: a.title, prompt: a.prompt ?? prompt })) };
      const result = mode === "evaluate" ? await api.evaluate(body) : await api.compare(body);
      if (mode === "evaluate") setEvaluation(result);
      else setComparison(result);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Evaluation failed.");
    } finally {
      setIsEvaluating(false);
    }
  }, [assets, prompt]);

  /* ── render ─────────────────────────────────────────────────── */
  return (
    <main className="studioPage">
      {/* Top bar */}
      <nav className="topbar" aria-label="Product">
        <div className="brand">
          <button type="button" className="backBtn" onClick={() => router.push("/")} aria-label="Back to home">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none"><path d="M12 4l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </button>
          <span className="brandMark">AC</span>
          <div className="scenarioPicker">
            <button
              type="button"
              className="scenarioPickerBtn"
              onClick={() => setScenarioPickerOpen(!scenarioPickerOpen)}
              aria-expanded={scenarioPickerOpen}
              aria-haspopup="listbox"
            >
              <span>{scenario.name}</span>
              <svg width="14" height="14" viewBox="0 0 20 20" fill="none"><path d="M6 8l4 4 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </button>
            {scenarioPickerOpen && (
              <>
                <div className="scenarioPickerBackdrop" onClick={() => setScenarioPickerOpen(false)} />
                <ul className="scenarioPickerMenu" role="listbox">
                  {scenarios.map((s) => (
                    <li key={s.id} role="option" aria-selected={s.id === scenarioId}>
                      <button
                        type="button"
                        className={`scenarioPickerItem${s.id === scenarioId ? " active" : ""}`}
                        onClick={() => {
                          setScenarioPickerOpen(false);
                          if (s.id !== scenarioId) router.push(`/studio/${encodeURIComponent(s.id)}`);
                        }}
                      >
                        <strong>{s.name}</strong>
                        <span>{s.defaultModel}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>
        {job && <span className="jobPill">{statusCopy[job.status] ?? job.status}</span>}
      </nav>

      {notice && <div className="notice">{notice}</div>}

      <div className="studioLayout">
        {/* Collapsible sidebar */}
        <aside className={`sidebar ${sidebarOpen ? "open" : "collapsed"}`}>
          <button type="button" className="sidebarToggle" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label={sidebarOpen ? "Collapse settings" : "Expand settings"}>
            <svg width="16" height="16" viewBox="0 0 20 20" fill="none"><path d={sidebarOpen ? "M13 4l-6 6 6 6" : "M7 4l6 6-6 6"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            {sidebarOpen && <span>Settings</span>}
          </button>

          {sidebarOpen && (
            <div className="sidebarBody">
              <label className="sField">
                <span>Model</span>
                {scenario.modelOptions.length ? (
                  <select value={model} onChange={(e) => setModel(e.target.value)} disabled={Boolean(scenario.forcedModel)}>
                    {scenario.modelOptions.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input value={model} onChange={(e) => setModel(e.target.value)} disabled={Boolean(scenario.forcedModel)} />
                )}
              </label>
              <label className="sField">
                <span>Image count</span>
                <input type="number" min={1} max={4} value={assetCount} onChange={(e) => setAssetCount(Number(e.target.value))} />
              </label>
              <label className="sField">
                <span>Size</span>
                <select value={size} onChange={(e) => setSize(e.target.value)}>
                  <option>1024x1024</option>
                  <option>1024x1792</option>
                  <option>1792x1024</option>
                </select>
              </label>
              <label className="sField">
                <span>Style</span>
                <input value={style} onChange={(e) => setStyle(e.target.value)} />
              </label>

              {scenario.id === "brand-template" && (
                <>
                  <label className="sField">
                    <span>Brand colors (comma-separated)</span>
                    <input value={brandColorsText} onChange={(e) => setBrandColorsText(e.target.value)} placeholder="#0078D4, #FFFFFF" />
                  </label>
                  <label className="sField">
                    <span>Font style</span>
                    <input value={fontStyle} onChange={(e) => setFontStyle(e.target.value)} placeholder="modern sans-serif" />
                  </label>
                  <label className="sField">
                    <span>Tone</span>
                    <input value={tone} onChange={(e) => setTone(e.target.value)} placeholder="trustworthy" />
                  </label>
                  <label className="sField">
                    <span>Logo description</span>
                    <input value={logoDescription} onChange={(e) => setLogoDescription(e.target.value)} placeholder="optional" />
                  </label>
                </>
              )}

              {scenario.id === "text-rendering" && (
                <label className="sField">
                  <span>Text to render</span>
                  <textarea value={textToRender} onChange={(e) => setTextToRender(e.target.value)} rows={4} />
                </label>
              )}

              {scenario.id === "aspect-ratio-package" && (
                <div className="sField">
                  <span>Formats</span>
                  <div className="checkGrid">
                    {[
                      ["instagram_square", "Instagram square"],
                      ["instagram_story", "Instagram story"],
                      ["linkedin_banner", "LinkedIn banner"],
                      ["desktop_hero", "Desktop hero"],
                      ["mobile_story", "Mobile story"],
                    ].map(([value, label]) => (
                      <label key={value} className="checkItem">
                        <input
                          type="checkbox"
                          checked={selectedFormats.includes(value)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedFormats((prev) => (prev.includes(value) ? prev : [...prev, value]));
                              return;
                            }
                            setSelectedFormats((prev) => prev.filter((item) => item !== value));
                          }}
                        />
                        <span>{label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {scenario.id === "product-placement" && (
                <label className="sField">
                  <span>Environments (one per line)</span>
                  <textarea value={environmentsText} onChange={(e) => setEnvironmentsText(e.target.value)} rows={4} />
                </label>
              )}

              {scenario.id === "multi-turn-refinement" && (
                <label className="sField">
                  <span>Refinement steps (one per line)</span>
                  <textarea value={refinementsText} onChange={(e) => setRefinementsText(e.target.value)} rows={4} />
                </label>
              )}

              {scenario.examples.length > 0 && (
                <div className="exampleSection">
                  <label className="sField">
                    <span>Example prompts</span>
                    <select
                      value={selectedExample}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSelectedExample(val);
                        if (val !== "Custom") {
                          const idx = parseInt(val, 10);
                          setPrompt(scenario.examples[idx]);
                        }
                      }}
                    >
                      <option value="Custom">Custom</option>
                      {scenario.examples.map((ex, i) => (
                        <option key={i} value={String(i)}>
                          Example prompt {i + 1}
                        </option>
                      ))}
                    </select>
                  </label>
                  {selectedExample !== "Custom" && (
                    <p className="examplePreview">{scenario.examples[parseInt(selectedExample, 10)]}</p>
                  )}
                </div>
              )}

              {readStringArray(selectedExtra.sample_images).length > 0 && (
                <div className="exampleSection">
                  <label className="checkItem">
                    <input type="checkbox" checked={useSampleInputs} onChange={(e) => setUseSampleInputs(e.target.checked)} />
                    <span>Use sample input images</span>
                  </label>
                  {useSampleInputs && (
                    <div className="samplePreviewGrid">
                      {readStringArray(selectedExtra.sample_images).map((path) => (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img key={path} src={sampleAssetUrl(path)} alt={path.split("/").pop() ?? "sample input"} />
                      ))}
                      {readString(selectedExtra.sample_images_mask) && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={sampleAssetUrl(readString(selectedExtra.sample_images_mask))} alt="sample mask" />
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </aside>

        {/* Main workspace */}
        <section className="workspace">
          {/* Prompt area */}
          <div className="promptCard">
            <label className="promptLabel">Prompt</label>
            <textarea
              className="promptInput"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={5}
              placeholder="Describe the image you want to create…"
            />
            <div className="promptActions">
              <button type="button" className="improveBtn" onClick={improvePrompt} disabled={isImproving}>
                <svg width="16" height="16" viewBox="0 0 20 20" fill="none"><path d="M10 2l2.09 6.26L18 10l-5.91 1.74L10 18l-2.09-6.26L2 10l5.91-1.74L10 2z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/></svg>
                {isImproving ? "Improving…" : "Improve with AI"}
              </button>
              <button type="button" className="generateBtn" onClick={generateAssets} disabled={isGenerating || !prompt}>
                {isGenerating ? "Generating…" : "Generate Assets"}
              </button>
            </div>
          </div>

          {/* Gallery */}
          {assets.length > 0 && (
            <div className="galleryArea">
              <div className="galleryHeader">
                <h2>Generated Assets</h2>
                <button type="button" className="evalTrigger" onClick={() => runEvaluation("evaluate")} disabled={isEvaluating}>
                  {isEvaluating ? "Evaluating…" : "Evaluate Selected Set"}
                </button>
              </div>
              <div className="gallery">
                {assets.map((asset) => (
                  <article className="assetCard" key={asset.id}>
                    {asset.url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        alt={asset.title}
                        src={asset.url}
                        onClick={() => setLightboxUrl(asset.url!)}
                        style={{ cursor: "pointer" }}
                      />
                    ) : (
                      <div className="assetPlaceholder"><span>{asset.title}</span></div>
                    )}
                    {asset.url && (
                      <button
                        type="button"
                        className="expandBtn"
                        onClick={() => setLightboxUrl(asset.url!)}
                        aria-label="View full size"
                      >
                        <svg width="14" height="14" viewBox="0 0 20 20" fill="none"><path d="M3 3h5M3 3v5M3 3l5 5M17 17h-5m5 0v-5m0 5l-5-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
                      </button>
                    )}
                    <div className="assetMeta">
                      <h3>{asset.title}</h3>
                      <p>{asset.prompt ?? prompt}</p>
                      <small>{asset.status ?? "ready"}</small>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {!assets.length && !isGenerating && (
            <div className="emptyState">
              <div className="emptyIcon">🖼️</div>
              <h3>No assets yet</h3>
              <p>Write a prompt above and click Generate Assets to get started.</p>
            </div>
          )}

          {/* Evaluation results */}
          {(evaluation || comparison) && (
            <div className="evalResults">
              <h2>Evaluation Results</h2>
              {Boolean(evaluation?.error || comparison?.error) && (
                <div className="notice">{String(evaluation?.error ?? comparison?.error)}</div>
              )}
              {(() => {
                const reports = (comparison?.ranked ?? comparison?.reports ?? evaluation?.reports) as Array<Record<string, unknown>> | undefined;
                if (!reports?.length) return null;
                return reports.map((entry, i) => {
                  const report = entry.report as Record<string, unknown> | undefined;
                  if (!report) return null;
                  const composite = typeof report.composite_score === "number" ? report.composite_score : null;
                  const embedding = report.embedding as Record<string, unknown> | undefined;
                  const rubric = report.rubric as Record<string, unknown> | undefined;
                  const judge = report.llm_judge as Record<string, unknown> | undefined;
                  const decision = report.threshold_decision as string | undefined;
                  const assetName = String(entry.name ?? `Asset ${i + 1}`);
                  return (
                    <div key={String(entry.asset_id ?? i)} className="evalReportCard">
                      <h3>{assetName}</h3>
                      <div className="scoreRow">
                        <ScoreCard
                          label="Composite"
                          value={composite !== null ? `${Math.round(composite * 100)}%` : "—"}
                          highlight
                          onDeepDive={() =>
                            setDetailModal({
                              title: "Composite evaluation",
                              subtitle: assetName,
                              body: <CompositeDetails report={report} />
                            })
                          }
                        />
                        <ScoreCard
                          label="Embedding"
                          value={formatLayerScore(embedding)}
                          onDeepDive={() =>
                            setDetailModal({
                              title: "Embedding similarity",
                              subtitle: assetName,
                              body: <EmbeddingDetails embedding={embedding} />
                            })
                          }
                        />
                        <ScoreCard
                          label="Rubric"
                          value={formatLayerScore(rubric)}
                          onDeepDive={() =>
                            setDetailModal({
                              title: "Prompt rubric deep dive",
                              subtitle: assetName,
                              body: <RubricDetails rubric={rubric} />
                            })
                          }
                        />
                        <ScoreCard
                          label="LLM Judge"
                          value={formatLayerScore(judge)}
                          onDeepDive={() =>
                            setDetailModal({
                              title: "LLM judge deep dive",
                              subtitle: assetName,
                              body: <JudgeDetails judge={judge} />
                            })
                          }
                        />
                        <ScoreCard
                          label="Decision"
                          value={decision ?? "—"}
                          highlight={decision === "accept"}
                          onDeepDive={() =>
                            setDetailModal({
                              title: "Threshold decision",
                              subtitle: assetName,
                              body: <DecisionDetails report={report} />
                            })
                          }
                        />
                      </div>
                      {judge && typeof (judge as Record<string, unknown>).overall_impression === "string" && (
                        <div className="recommendation">
                          <strong>Judge notes</strong>
                          <p>{String((judge as Record<string, unknown>).overall_impression)}</p>
                        </div>
                      )}
                    </div>
                  );
                });
              })()}
            </div>
          )}
        </section>
      </div>

      {/* Lightbox modal */}
      {lightboxUrl && (
        <div className="lightbox" onClick={() => setLightboxUrl(null)}>
          <button type="button" className="lightboxClose" onClick={() => setLightboxUrl(null)} aria-label="Close">
            <svg width="24" height="24" viewBox="0 0 20 20" fill="none"><path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
          </button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={lightboxUrl} alt="Full size preview" className="lightboxImg" onClick={(e) => e.stopPropagation()} />
        </div>
      )}

      {detailModal && (
        <div className="detailOverlay" role="presentation" onClick={() => setDetailModal(null)}>
          <section
            className="detailModal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="detail-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="detailHeader">
              <div>
                <p className="eyebrow">Evaluation detail</p>
                <h2 id="detail-title">{detailModal.title}</h2>
                {detailModal.subtitle && <p>{detailModal.subtitle}</p>}
              </div>
              <button type="button" className="detailClose" onClick={() => setDetailModal(null)} aria-label="Close details">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
              </button>
            </div>
            <div className="detailBody">{detailModal.body}</div>
          </section>
        </div>
      )}
    </main>
  );
}

function formatLayerScore(layer: Record<string, unknown> | undefined): string {
  if (!layer) return "—";
  // Embedding layer → cosine_similarity (0–1)
  if (typeof layer.cosine_similarity === "number") return `${Math.round(layer.cosine_similarity * 100)}%`;
  // Rubric layer → rubric_score (0–1)
  if (typeof layer.rubric_score === "number") return `${Math.round(layer.rubric_score * 100)}%`;
  // LLM Judge layer → average_score (1–5)
  if (typeof layer.average_score === "number") return `${(layer.average_score as number).toFixed(1)} / 5`;
  return "—";
}

function readString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function readStringArray(value: unknown, fallback: string[] = []): string[] {
  if (!Array.isArray(value)) return fallback;
  return value.map(String).filter(Boolean);
}

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitLines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function sampleAssetUrl(path: string): string {
  return `${API_BASE_URL}/assets/samples/${path}`;
}

async function samplePathToAssetInput(path: string): Promise<{ name: string; data: string }> {
  const response = await fetch(sampleAssetUrl(path));
  if (!response.ok) {
    throw new Error(`Failed to load sample image: ${path}`);
  }
  const contentType = response.headers.get("content-type") ?? "image/png";
  const bytes = new Uint8Array(await response.arrayBuffer());
  let binary = "";
  for (let index = 0; index < bytes.length; index += 1) {
    binary += String.fromCharCode(bytes[index]);
  }
  const base64 = btoa(binary);
  return {
    name: path.split("/").pop() ?? "sample.png",
    data: `data:${contentType};base64,${base64}`,
  };
}

function ScoreCard({
  label,
  value,
  highlight = false,
  onDeepDive
}: {
  label: string;
  value: string;
  highlight?: boolean;
  onDeepDive?: () => void;
}) {
  return (
    <div className={`scoreCard${highlight ? " highlight" : ""}`}>
      <div className="scoreCardTop">
        <span>{label}</span>
        {onDeepDive && (
          <button
            type="button"
            className="deepDiveBtn"
            onClick={onDeepDive}
            aria-label={`Open ${label} details`}
            title={`Open ${label} details`}
          >
            <svg width="15" height="15" viewBox="0 0 20 20" fill="none"><circle cx="9" cy="9" r="5.5" stroke="currentColor" strokeWidth="1.7"/><path d="M13 13l4 4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
          </button>
        )}
      </div>
      <strong>{value}</strong>
    </div>
  );
}

function CompositeDetails({ report }: { report: Record<string, unknown> }) {
  const weights = asRecord(report.weights);
  return (
    <div className="detailStack">
      <dl className="detailGrid">
        <DetailItem label="Composite score" value={formatPercent(report.composite_score)} />
        <DetailItem label="Layers run" value={readStringArray(report.layers_run).join(", ") || "—"} />
        <DetailItem label="Model used" value={String(report.model_used ?? "—")} />
        <DetailItem label="Evaluation time" value={typeof report.evaluation_time_ms === "number" ? `${report.evaluation_time_ms} ms` : "—"} />
      </dl>
      <DetailSection title="Weights">
        <KeyValueList value={weights} />
      </DetailSection>
      <DetailSection title="Threshold reasons">
        <ReasonList reasons={readStringArray(report.threshold_reasons)} />
      </DetailSection>
    </div>
  );
}

function EmbeddingDetails({ embedding }: { embedding: Record<string, unknown> | undefined }) {
  if (!embedding) return <EmptyDetail message="Embedding evaluation was not run for this asset." />;
  return (
    <div className="detailStack">
      <dl className="detailGrid">
        <DetailItem label="Cosine similarity" value={formatPercent(embedding.cosine_similarity)} />
        <DetailItem label="Prompt vector model" value={String(embedding.model ?? "—")} />
      </dl>
      <DetailSection title="Raw embedding metrics">
        <KeyValueList value={embedding} />
      </DetailSection>
    </div>
  );
}

function RubricDetails({ rubric }: { rubric: Record<string, unknown> | undefined }) {
  if (!rubric) return <EmptyDetail message="Rubric evaluation was not run for this asset." />;
  const attributes = Array.isArray(rubric.attributes) ? rubric.attributes : [];
  return (
    <div className="detailStack">
      <dl className="detailGrid">
        <DetailItem label="Rubric score" value={formatPercent(rubric.rubric_score)} />
        <DetailItem label="Matched" value={`${String(rubric.matched_attributes ?? 0)} / ${String(rubric.total_attributes ?? attributes.length)}`} />
        <DetailItem label="Partial" value={String(rubric.partial_attributes ?? 0)} />
      </dl>
      <DetailSection title="Questions and results">
        {attributes.length ? (
          <div className="rubricTable" role="table" aria-label="Rubric questions and results">
            <div className="rubricHeader" role="row">
              <span>Category</span>
              <span>Question / parameter</span>
              <span>Result</span>
              <span>Confidence</span>
              <span>Reasoning</span>
            </div>
            {attributes.map((item, index) => {
              const attribute = asRecord(item) ?? {};
              return (
                <div className="rubricRow" role="row" key={`${String(attribute.question ?? "question")}-${index}`}>
                  <span>{String(attribute.category ?? "—")}</span>
                  <span>
                    <strong>{String(attribute.description ?? "—")}</strong>
                    <small>{String(attribute.question ?? "—")}</small>
                  </span>
                  <span className={`answerPill ${String(attribute.answer ?? "").toLowerCase()}`}>{String(attribute.answer ?? "—")}</span>
                  <span>{formatPercent(attribute.confidence)}</span>
                  <span>{String(attribute.reasoning ?? "—")}</span>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyDetail message="No rubric attributes were returned." />
        )}
      </DetailSection>
    </div>
  );
}

function JudgeDetails({ judge }: { judge: Record<string, unknown> | undefined }) {
  if (!judge) return <EmptyDetail message="LLM judge evaluation was not run for this asset." />;
  const criteria = [
    ["Visual quality", "visual_quality"],
    ["Spatial coherence", "spatial_coherence"],
    ["Style fidelity", "style_fidelity"],
    ["Aesthetic appeal", "aesthetic_appeal"],
    ["Text legibility", "text_legibility"]
  ] as const;
  return (
    <div className="detailStack">
      <dl className="detailGrid">
        <DetailItem label="Average score" value={typeof judge.average_score === "number" ? `${judge.average_score.toFixed(1)} / 5` : "—"} />
      </dl>
      <DetailSection title="Criteria">
        <div className="judgeList">
          {criteria.map(([label, key]) => {
            const criterion = asRecord(judge[key]);
            if (!criterion) return null;
            return (
              <article className="judgeItem" key={key}>
                <div>
                  <strong>{label}</strong>
                  <span>{typeof criterion.score === "number" ? `${criterion.score} / 5` : "—"}</span>
                </div>
                <p>{String(criterion.justification ?? "—")}</p>
              </article>
            );
          })}
        </div>
      </DetailSection>
      <DetailSection title="Overall impression">
        <p className="detailText">{String(judge.overall_impression ?? "—")}</p>
      </DetailSection>
    </div>
  );
}

function DecisionDetails({ report }: { report: Record<string, unknown> }) {
  return (
    <div className="detailStack">
      <dl className="detailGrid">
        <DetailItem label="Decision" value={String(report.threshold_decision ?? "—")} />
        <DetailItem label="Composite score" value={formatPercent(report.composite_score)} />
      </dl>
      <DetailSection title="Reasons">
        <ReasonList reasons={readStringArray(report.threshold_reasons)} />
      </DetailSection>
    </div>
  );
}

function DetailSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="detailSection">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function ReasonList({ reasons }: { reasons: string[] }) {
  if (!reasons.length) return <EmptyDetail message="No threshold reasons were returned." />;
  return (
    <ul className="reasonList">
      {reasons.map((reason) => (
        <li key={reason}>{reason}</li>
      ))}
    </ul>
  );
}

function KeyValueList({ value }: { value: Record<string, unknown> | undefined }) {
  if (!value || !Object.keys(value).length) return <EmptyDetail message="No details were returned." />;
  return (
    <dl className="keyValueList">
      {Object.entries(value).map(([key, item]) => (
        <div key={key}>
          <dt>{humanizeKey(key)}</dt>
          <dd>{formatDetailValue(item)}</dd>
        </div>
      ))}
    </dl>
  );
}

function EmptyDetail({ message }: { message: string }) {
  return <p className="emptyDetail">{message}</p>;
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function formatPercent(value: unknown): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "—";
}

function formatDetailValue(value: unknown): string {
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(3);
  if (typeof value === "string") return value;
  if (typeof value === "boolean") return value ? "true" : "false";
  if (value === null || value === undefined) return "—";
  return JSON.stringify(value);
}

function humanizeKey(key: string): string {
  return key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
