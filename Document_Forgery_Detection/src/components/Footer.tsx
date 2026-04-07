import { Shield } from "lucide-react";

const Footer = () => (
  <footer className="border-t border-border/50 py-8">
    <div className="container mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
      <div className="flex items-center gap-2">
        <Shield className="h-5 w-5 text-primary" />
        <span className="font-display font-semibold text-foreground">ForgeGuard</span>
      </div>
      <p className="text-muted-foreground text-sm">
        © {new Date().getFullYear()} ForgeGuard. Document Forgery & Tampering Detection System.
      </p>
    </div>
  </footer>
);

export default Footer;
