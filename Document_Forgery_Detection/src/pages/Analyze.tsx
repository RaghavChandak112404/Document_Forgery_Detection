import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileImage, X, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "application/pdf"];
const API_URL = "/api";

const STAGE_LABELS = [
  "Running Error Level Analysis...",
  "Detecting edges and structure...",
  "Analysing texture and noise...",
  "Inspecting metadata...",
  "Calculating authenticity score...",
];

const AnalyzePage = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stageLabel, setStageLabel] = useState(STAGE_LABELS[0]);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback((f: File) => {
    if (!ACCEPTED_TYPES.includes(f.type)) {
      toast.error("Invalid file type. Please upload a PDF, JPG, or PNG document.");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      toast.error("File too large. Maximum size is 10MB.");
      return;
    }
    setFile(f);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(f);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    },
    [handleFile]
  );

  const handleAnalyze = async () => {
    if (!file || !preview) return;

    setAnalyzing(true);
    setProgress(0);

    // Animate progress while the real API call runs
    let currentStage = 0;
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const next = prev + Math.random() * 8 + 3;
        const newStage = Math.min(Math.floor(next / 20), STAGE_LABELS.length - 1);
        if (newStage !== currentStage) {
          currentStage = newStage;
          setStageLabel(STAGE_LABELS[newStage]);
        }
        return Math.min(next, 90); // cap at 90 until API responds
      });
    }, 250);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/verify-document`, {
        method: "POST",
        body: formData,
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(err.detail ?? "Analysis failed");
      }

      const result = await response.json();
      const finalImageUrl = result.originalImage || preview;
      setProgress(100);
      setStageLabel("Analysis complete!");

      setTimeout(() => {
        navigate("/results", {
          state: { imageUrl: finalImageUrl, fileName: file.name, apiResult: result },
        });
      }, 400);
    } catch (err: unknown) {
      clearInterval(progressInterval);
      setAnalyzing(false);
      setProgress(0);
      const message =
        err instanceof Error ? err.message : "Could not reach the analysis server.";
      toast.error(`Analysis failed: ${message}`);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-24 pb-16">
        <div className="container mx-auto px-4 max-w-3xl">
          <div className="text-center mb-10">
            <h1 className="font-display font-bold text-3xl md:text-4xl mb-3">
              Analyze <span className="text-gradient-primary">Document</span>
            </h1>
            <p className="text-muted-foreground">Upload a document image to detect tampering</p>
          </div>

          {/* Upload area */}
          {!preview && (
            <div
              className={`glass-card p-12 text-center cursor-pointer transition-all duration-200 ${
                dragOver ? "border-primary bg-primary/5 glow-primary" : "hover:border-primary/40"
              }`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => document.getElementById("file-input")?.click()}
            >
              <input
                id="file-input"
                type="file"
                accept=".jpg,.jpeg,.png,.pdf"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
              <Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="font-display font-semibold text-lg text-foreground mb-2">
                Drop your document here
              </p>
              <p className="text-muted-foreground text-sm">
                or click to browse · PDF, JPG, PNG · Max 10MB
              </p>
            </div>
          )}

          {/* Preview */}
          {preview && !analyzing && (
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <FileImage className="h-5 w-5 text-primary" />
                  <span className="text-foreground font-medium text-sm truncate max-w-[200px]">{file?.name}</span>
                </div>
                <button
                  onClick={() => { setFile(null); setPreview(null); }}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="relative rounded-lg overflow-hidden mb-6 bg-secondary/50 flex flex-col items-center justify-center min-h-[16rem]">
                {file?.type === "application/pdf" ? (
                  <div className="flex flex-col items-center justify-center p-8">
                    <FileText className="h-16 w-16 text-primary mb-4" />
                    <span className="text-lg font-medium text-foreground">PDF Document Ready</span>
                  </div>
                ) : (
                  <img src={preview} alt="Document preview" className="w-full max-h-96 object-contain" />
                )}
              </div>

              <Button variant="hero" size="lg" className="w-full" onClick={handleAnalyze}>
                Analyze Document
              </Button>
            </div>
          )}

          {/* Analyzing state */}
          {analyzing && (
            <div className="glass-card p-8">
              <div className="relative rounded-lg overflow-hidden mb-6 bg-secondary/50 flex flex-col items-center justify-center min-h-[16rem]">
                {file?.type === "application/pdf" ? (
                  <div className="flex flex-col items-center justify-center p-8 opacity-60">
                    <FileText className="h-16 w-16 text-primary mb-4" />
                    <span className="text-lg font-medium text-foreground">Analyzing PDF...</span>
                  </div>
                ) : (
                  <img src={preview!} alt="Analyzing" className="w-full max-h-80 object-contain opacity-60" />
                )}
                {/* Scan line */}
                <div className="absolute inset-0 overflow-hidden">
                  <div className="absolute top-0 bottom-0 w-1 bg-gradient-to-b from-transparent via-cyan to-transparent animate-scan" />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground font-medium">{stageLabel}</span>
                  <span className="text-cyan font-display font-semibold">{Math.min(Math.round(progress), 100)}%</span>
                </div>
                <Progress value={Math.min(progress, 100)} className="h-2 bg-secondary [&>div]:bg-gradient-to-r [&>div]:from-primary [&>div]:to-cyan" />
                <p className="text-xs text-muted-foreground">
                  Running ELA, edge detection, and texture analysis…
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default AnalyzePage;
