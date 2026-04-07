import { FileSearch, Layers, Grid3X3, Shield } from "lucide-react";

const techniques = [
  {
    icon: FileSearch,
    title: "Error Level Analysis",
    description: "Detects compression inconsistencies that indicate image manipulation by analyzing JPEG compression artifacts across different regions.",
  },
  {
    icon: Layers,
    title: "Edge Detection",
    description: "Identifies unnatural boundaries and splicing artifacts by applying Canny and Sobel operators to reveal hidden manipulation edges.",
  },
  {
    icon: Grid3X3,
    title: "Texture Analysis",
    description: "Analyzes surface patterns and noise distributions using statistical methods to detect regions with inconsistent texture characteristics.",
  },
  {
    icon: Shield,
    title: "Combined Verdict",
    description: "Aggregates all detection methods with weighted scoring to provide a comprehensive tampering probability assessment.",
  },
];

const AboutSection = () => {
  return (
    <section id="about" className="py-24 relative">
      <div className="absolute inset-0 bg-gradient-to-b from-background via-secondary/20 to-background pointer-events-none" />

      <div className="relative container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="font-display font-bold text-3xl md:text-4xl mb-4">
            How It <span className="text-gradient-primary">Works</span>
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
            Our system combines multiple forensic techniques to detect even the most sophisticated document tampering attempts.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {techniques.map((tech, index) => (
            <div
              key={tech.title}
              className="glass-card p-6 hover:border-primary/40 transition-all duration-300 group"
              style={{ animation: `fade-in-up 0.6s ease-out ${index * 0.1}s both` }}
            >
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                <tech.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2 text-foreground">{tech.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{tech.description}</p>
            </div>
          ))}
        </div>

        {/* What is Document Forgery */}
        <div className="mt-20 glass-card p-8 md:p-12">
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-display font-bold text-2xl mb-4 text-foreground">What is Document Forgery?</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                Document forgery involves the unauthorized alteration or fabrication of documents to deceive. This includes modifying text, replacing photos, altering signatures, or splicing elements from different sources.
              </p>
              <p className="text-muted-foreground leading-relaxed">
                Modern image editing tools make forgeries increasingly convincing to the human eye, making automated forensic analysis essential for verification.
              </p>
            </div>
            <div>
              <h3 className="font-display font-bold text-2xl mb-4 text-foreground">Why Automated Detection?</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                Human inspection alone is unreliable against sophisticated forgeries. Our system analyzes pixel-level artifacts, compression patterns, and statistical anomalies that are invisible to the naked eye.
              </p>
              <p className="text-muted-foreground leading-relaxed">
                Each technique targets different manipulation signatures, and combining them produces highly accurate and reliable results.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
