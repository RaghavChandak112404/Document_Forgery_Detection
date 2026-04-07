import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import {
  Download,
  AlertTriangle,
  CheckCircle,
  ArrowLeft,
  Eye,
  Layers,
  Grid3X3,
  FileSearch,
  HelpCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

// ── Types matching the backend response ──────────────────────────────────────

type Severity = "high" | "medium" | "low";

interface Finding {
  technique: string;
  finding: string;
  severity: Severity;
  score: number;
}

interface ApiResult {
  authenticity_score: number;
  verdict: string;
  confidence: number;
  suspiciousRegions: number;
  analysisTime: number;
  flags: string[];
  details: Finding[];
  breakdown: {
    ela_score: number;
    edge_score: number;
    noise_score: number;
    meta_score: number;
  };
  processedImages: {
    ela: string;
    edges: string;
    texture: string;
  };
}

type AnalysisMode = "ela" | "edges" | "texture";

// ── Static mode metadata ─────────────────────────────────────────────────────

const modeInfo: Record<
  AnalysisMode,
  { label: string; icon: typeof FileSearch; description: string; color: string }
> = {
  ela: {
    label: "ELA",
    icon: FileSearch,
    description:
      "Error Level Analysis highlights compression inconsistencies from image editing",
    color: "text-primary",
  },
  edges: {
    label: "Edge Detection",
    icon: Layers,
    description:
      "Canny edge detection reveals unnatural boundaries from splicing",
    color: "text-cyan",
  },
  texture: {
    label: "Texture Analysis",
    icon: Grid3X3,
    description:
      "Statistical texture analysis detects noise pattern inconsistencies",
    color: "text-rose",
  },
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function verdictStyle(verdict: string) {
  if (verdict === "LIKELY GENUINE")
    return { icon: CheckCircle, color: "text-cyan", glowClass: "glow-cyan", label: "Likely Genuine" };
  if (verdict === "LIKELY FAKE")
    return { icon: AlertTriangle, color: "text-rose", glowClass: "glow-rose", label: "Likely Fake" };
  return { icon: HelpCircle, color: "text-primary", glowClass: "", label: "Inconclusive" };
}

function severityColor(s: Severity) {
  return s === "high" ? "bg-rose" : s === "medium" ? "bg-primary" : "bg-cyan";
}

function scoreBar(score: number) {
  // authenticity_score: high = genuine, colour accordingly
  const pct = Math.round(score);
  const col =
    score >= 70
      ? "from-cyan to-cyan"
      : score >= 45
      ? "from-primary to-primary"
      : "from-rose to-rose";
  return { pct, col };
}

// ── Component ────────────────────────────────────────────────────────────────

const ResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    imageUrl,
    fileName,
    apiResult,
  } = (location.state as {
    imageUrl: string;
    fileName: string;
    apiResult: ApiResult;
  }) || {};

  const [activeMode, setActiveMode] = useState<AnalysisMode>("ela");
  const [sliderPos, setSliderPos] = useState(50);

  // ── No data guard ──────────────────────────────────────────────────────────
  if (!imageUrl || !apiResult) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-muted-foreground mb-4">No analysis results found.</p>
            <Button variant="hero" asChild>
              <Link to="/analyze">Upload a Document</Link>
            </Button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const vs = verdictStyle(apiResult.verdict);
  const VerdictIcon = vs.icon;

  // Processed image for the active mode (falls back to original if backend
  // didn't return one)
  const processedSrc =
    (apiResult.processedImages?.[activeMode]) || imageUrl;

  const { pct: authPct, col: authCol } = scoreBar(apiResult.authenticity_score);

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-24 pb-16">
        <div className="container mx-auto px-4">

          {/* Header */}
          <div className="flex items-center gap-4 mb-8">
            <button
              onClick={() => navigate("/analyze")}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="font-display font-bold text-2xl md:text-3xl">
                Analysis Results
              </h1>
              <p className="text-muted-foreground text-sm">{fileName}</p>
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">

            {/* ── Left: Image Comparison ────────────────────────────────── */}
            <div className="lg:col-span-2">
              <div className="glass-card p-6">

                {/* Mode toggles */}
                <div className="flex flex-wrap gap-2 mb-6">
                  {(
                    Object.entries(modeInfo) as [
                      AnalysisMode,
                      (typeof modeInfo)[AnalysisMode]
                    ][]
                  ).map(([key, mode]) => (
                    <Tooltip key={key}>
                      <TooltipTrigger asChild>
                        <button
                          onClick={() => setActiveMode(key)}
                          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                            activeMode === key
                              ? "bg-primary/20 border border-primary/40 text-foreground"
                              : "bg-secondary/50 border border-transparent text-muted-foreground hover:text-foreground hover:bg-secondary"
                          }`}
                        >
                          <mode.icon
                            className={`h-4 w-4 ${
                              activeMode === key ? mode.color : ""
                            }`}
                          />
                          {mode.label}
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>{mode.description}</TooltipContent>
                    </Tooltip>
                  ))}
                </div>

                {/* A/B Comparison Slider */}
                <div
                  className="relative rounded-lg overflow-hidden bg-secondary/30"
                  style={{ aspectRatio: "4/3" }}
                >
                  {/* Original (left side) */}
                  <div className="absolute inset-0">
                    <img
                      src={imageUrl}
                      alt="Original"
                      className="w-full h-full object-contain"
                    />
                  </div>

                  {/* Processed overlay (right side) — real backend image */}
                  <div
                    className="absolute inset-0 overflow-hidden"
                    style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}
                  >
                    <img
                      src={processedSrc}
                      alt="Processed"
                      className="w-full h-full object-contain"
                      // CSS fallback filter if no backend image returned
                      style={
                        processedSrc === imageUrl
                          ? {
                              filter:
                                activeMode === "ela"
                                  ? "contrast(3) saturate(2) hue-rotate(180deg)"
                                  : activeMode === "edges"
                                  ? "invert(1) grayscale(1) contrast(5)"
                                  : "saturate(3) contrast(2) brightness(0.8)",
                            }
                          : undefined
                      }
                    />
                  </div>

                  {/* Slider handle */}
                  <div
                    className="absolute top-0 bottom-0 w-1 bg-cyan cursor-ew-resize z-10"
                    style={{ left: `${sliderPos}%` }}
                  >
                    <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 bg-cyan rounded-full flex items-center justify-center glow-cyan">
                      <Eye className="h-4 w-4 text-accent-foreground" />
                    </div>
                  </div>

                  {/* Invisible range input for drag */}
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={sliderPos}
                    onChange={(e) => setSliderPos(Number(e.target.value))}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-20"
                  />

                  {/* Labels */}
                  <div className="absolute bottom-3 left-3 bg-background/80 backdrop-blur px-3 py-1 rounded text-xs font-medium text-foreground">
                    Original
                  </div>
                  <div className="absolute bottom-3 right-3 bg-background/80 backdrop-blur px-3 py-1 rounded text-xs font-medium text-foreground">
                    {modeInfo[activeMode].label}
                  </div>
                </div>

                {/* Score breakdown bars */}
                <div className="mt-6 space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    Layer scores
                  </p>
                  {[
                    { label: "ELA",              val: apiResult.breakdown.ela_score },
                    { label: "Edge Detection",   val: apiResult.breakdown.edge_score },
                    { label: "Texture Analysis", val: apiResult.breakdown.noise_score },
                    { label: "Metadata",         val: apiResult.breakdown.meta_score },
                  ].map(({ label, val }) => {
                    const { pct, col } = scoreBar(val);
                    return (
                      <div key={label} className="flex items-center gap-3 text-sm">
                        <span className="w-32 text-muted-foreground shrink-0">{label}</span>
                        <div className="flex-1 h-1.5 bg-secondary rounded-full overflow-hidden">
                          <div
                            className={`h-full bg-gradient-to-r ${col} rounded-full`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="w-10 text-right font-semibold text-foreground">
                          {pct}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* ── Right: Results Panel ──────────────────────────────────── */}
            <div className="space-y-4">

              {/* Verdict card */}
              <div className={`glass-card p-6 ${vs.glowClass}`}>
                <div className="flex items-center gap-3 mb-4">
                  <VerdictIcon className={`h-6 w-6 ${vs.color}`} />
                  <h3 className="font-display font-semibold text-lg text-foreground">
                    {vs.label}
                  </h3>
                </div>
                <p className="text-muted-foreground text-sm mb-4">
                  {apiResult.verdict === "LIKELY GENUINE"
                    ? `Document appears authentic (${authPct}/100 authenticity score)`
                    : apiResult.verdict === "LIKELY FAKE"
                    ? `Tampering detected — authenticity score ${authPct}/100`
                    : `Result is inconclusive — authenticity score ${authPct}/100`}
                </p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className={`h-full bg-gradient-to-r ${authCol} rounded-full`}
                      style={{ width: `${authPct}%` }}
                    />
                  </div>
                  <span className={`text-sm font-display font-semibold ${vs.color}`}>
                    {authPct}
                  </span>
                </div>
              </div>

              {/* Summary stats */}
              <div className="glass-card p-6">
                <h3 className="font-display font-semibold mb-4 text-foreground">
                  Summary
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Suspicious layers</span>
                    <span
                      className={`font-semibold ${
                        apiResult.suspiciousRegions > 0 ? "text-rose" : "text-cyan"
                      }`}
                    >
                      {apiResult.suspiciousRegions} / 4
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Techniques used</span>
                    <span className="font-semibold text-foreground">4</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Analysis time</span>
                    <span className="font-semibold text-cyan">
                      {apiResult.analysisTime}s
                    </span>
                  </div>
                </div>
              </div>

              {/* Findings */}
              <div className="glass-card p-6">
                <h3 className="font-display font-semibold mb-4 text-foreground">
                  Findings
                </h3>
                <div className="space-y-3">
                  {apiResult.details.map((d, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-lg bg-secondary/50 border border-border/50"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={`w-2 h-2 rounded-full ${severityColor(
                            d.severity
                          )}`}
                        />
                        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                          {d.technique}
                        </span>
                        <span className="ml-auto text-xs text-muted-foreground">
                          {d.score}/100
                        </span>
                      </div>
                      <p className="text-sm text-foreground">{d.finding}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <Button
                  variant="cyan"
                  className="flex-1 gap-2"
                  onClick={() => {
                    const blob = new Blob(
                      [JSON.stringify(apiResult, null, 2)],
                      { type: "application/json" }
                    );
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `document-guard-report-${Date.now()}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                >
                  <Download className="h-4 w-4" />
                  Download Report
                </Button>
                <Button variant="outline" asChild>
                  <Link to="/analyze">New Scan</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default ResultsPage;
