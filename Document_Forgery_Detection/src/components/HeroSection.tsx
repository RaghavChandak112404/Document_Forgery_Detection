import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Upload, Shield, Scan, FileSearch } from "lucide-react";
import heroIllustration from "@/assets/hero-illustration.png";

const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center grid-bg overflow-hidden">
      {/* Gradient overlays */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-background/90 to-background pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px]" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-cyan/5 rounded-full blur-[100px]" />

      <div className="relative container mx-auto px-4 pt-24 pb-16">
        <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-16">
          {/* Left content */}
          <div className="flex-1 text-center lg:text-left" style={{ animation: "fade-in-up 0.6s ease-out forwards" }}>
            <div className="inline-flex items-center gap-2 glass-card px-4 py-2 mb-6">
              <Shield className="h-4 w-4 text-cyan" />
              <span className="text-sm text-muted-foreground">AI-Powered Document Analysis</span>
            </div>

            <h1 className="font-display font-bold text-4xl md:text-5xl lg:text-6xl leading-tight mb-6">
              Detect Document{" "}
              <span className="text-gradient-primary">Forgery</span>{" "}
              in Seconds
            </h1>

            <p className="text-muted-foreground text-lg md:text-xl max-w-xl mx-auto lg:mx-0 mb-8 leading-relaxed">
              Advanced computer vision system to identify tampered regions in documents using ELA, edge detection, and texture analysis.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <Button variant="hero" size="lg" asChild>
                <Link to="/analyze" className="gap-2">
                  <Upload className="h-5 w-5" />
                  Upload Document
                </Link>
              </Button>
              <Button 
                variant="outline" 
                size="lg" 
                className="gap-2"
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                Learn More
              </Button>
            </div>

            {/* Stats section removed */}
          </div>

          {/* Right illustration */}
          <div className="flex-1 flex justify-center" style={{ animation: "fade-in-up 0.8s ease-out forwards" }}>
            <div className="relative">
              <div className="glass-card p-8 glow-primary">
                <img src={heroIllustration} alt="Document scanning visualization" className="w-full max-w-md" />
                {/* Scan line overlay */}
                <div className="absolute inset-0 overflow-hidden rounded-xl pointer-events-none">
                  <div className="absolute top-0 bottom-0 w-0.5 bg-gradient-to-b from-transparent via-cyan to-transparent animate-scan opacity-60" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
