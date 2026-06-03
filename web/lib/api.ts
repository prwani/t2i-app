export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type Scenario = {
  id: string;
  name: string;
  description: string;
  defaultModel: string;
  forcedModel?: string | null;
  modelOptions: string[];
  defaultPrompt: string;
  examples: string[];
  exampleExtras: Array<Record<string, unknown>>;
};

export type Asset = {
  id: string;
  title: string;
  url?: string;
  prompt?: string;
  status?: string;
  metadata?: Record<string, unknown>;
};

export type Job = {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed" | "completed" | string;
  message?: string;
  assets: Asset[];
};

type RequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
  signal?: AbortSignal;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    signal: options.signal,
    headers: {
      "Content-Type": "application/json"
    },
    body: options.body ? JSON.stringify(options.body) : undefined
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function pick<T>(value: unknown, fallback: T): T {
  return value === undefined || value === null ? fallback : (value as T);
}

export function normalizeScenario(raw: Record<string, unknown>): Scenario {
  const id = String(pick(raw.id ?? raw.slug, "general"));
  return {
    id,
    name: String(pick(raw.name ?? raw.label ?? raw.title, id)),
    description: String(pick(raw.description, "Create polished campaign-ready assets.")),
    defaultModel: String(pick(raw.defaultModel ?? raw.default_model ?? raw.model, "gpt-image-1")),
    forcedModel: (raw.forcedModel ?? raw.forced_model ?? null) as string | null,
    modelOptions: Array.isArray(raw.modelOptions)
      ? raw.modelOptions.map(String)
      : Array.isArray(raw.model_options)
        ? raw.model_options.map(String)
        : [],
    defaultPrompt: String(
      pick(
        raw.defaultPrompt ??
          raw.default_prompt ??
          raw.prompt ??
          (Array.isArray(raw.example_prompts) ? raw.example_prompts[0] : undefined),
        "Create a premium product visual."
      )
    ),
    examples: Array.isArray(raw.examples)
      ? raw.examples.map(String)
      : Array.isArray(raw.example_prompts)
        ? raw.example_prompts.map(String)
        : [],
    exampleExtras: Array.isArray(raw.exampleExtras)
      ? raw.exampleExtras.map((item) => (item as Record<string, unknown>) ?? {})
      : Array.isArray(raw.example_extras)
        ? raw.example_extras.map((item) => (item as Record<string, unknown>) ?? {})
        : []
  };
}

export function normalizeAsset(raw: unknown, index = 0): Asset {
  if (typeof raw === "string") {
    return { id: `asset-${index + 1}`, title: `Asset ${index + 1}`, url: raw };
  }

  const item = (raw ?? {}) as Record<string, unknown>;
  return {
    id: String(pick(item.id ?? item.asset_id, `asset-${index + 1}`)),
    title: String(pick(item.title ?? item.name, `Asset ${index + 1}`)),
    url: normalizeUrl((item.url ?? item.image_url ?? item.uri ?? item.path) as string | undefined),
    prompt: item.prompt as string | undefined,
    status: item.status as string | undefined,
    metadata: item.metadata as Record<string, unknown> | undefined
  };
}

export function normalizeJob(raw: Record<string, unknown>): Job {
  const jobId = String(pick(raw.job_id ?? raw.id, "local-preview"));
  const status = String(pick(raw.status, raw.assets || raw.images || raw.results ? "succeeded" : "queued"));
  const assetSource = raw.assets ?? raw.images ?? raw.results ?? [];
  const assets = Array.isArray(assetSource) ? assetSource.map(normalizeAsset) : [];

  return {
    id: jobId,
    status,
    message: raw.message as string | undefined,
    assets
  };
}

export const api = {
  health: () => request<Record<string, unknown>>("/health"),
  scenarios: async () => {
    const payload = await request<unknown>("/api/scenarios");
    const list = Array.isArray(payload)
      ? payload
      : Array.isArray((payload as Record<string, unknown>).scenarios)
        ? ((payload as Record<string, unknown>).scenarios as unknown[])
        : [];
    return list.map((item) => normalizeScenario(item as Record<string, unknown>));
  },
  improvePrompt: (body: { prompt: string; scenario: string }) =>
    request<{ improved_prompt?: string; prompt?: string; suggestions?: string[] }>("/api/prompts/improve", {
      method: "POST",
      body
    }),
  createGeneration: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>("/api/generations", { method: "POST", body }),
  getGeneration: (jobId: string, signal?: AbortSignal) =>
    request<Record<string, unknown>>(`/api/generations/${encodeURIComponent(jobId)}`, { signal }),
  evaluate: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>("/api/evaluations", { method: "POST", body }),
  compare: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>("/api/comparisons", { method: "POST", body })
};

function normalizeUrl(url: string | undefined) {
  if (!url || /^https?:\/\//.test(url) || url.startsWith("data:")) return url;
  return `${API_BASE_URL}${url.startsWith("/") ? url : `/${url}`}`;
}
