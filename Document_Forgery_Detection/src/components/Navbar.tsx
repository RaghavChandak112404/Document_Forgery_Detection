import { Link, useNavigate, useLocation } from "react-router-dom";
import { Shield, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const Navbar = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleAboutClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setMobileOpen(false);
    if (location.pathname !== "/") {
      navigate("/");
      setTimeout(() => {
        document.getElementById("about")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } else {
      document.getElementById("about")?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-card-strong border-b border-border/50">
      <div className="container mx-auto flex items-center justify-between h-16 px-4">
        <Link to="/" className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-primary" />
          <span className="font-display font-bold text-lg text-foreground">ForgeGuard</span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link to="/" className="text-muted-foreground hover:text-foreground transition-colors text-sm">Home</Link>
          <Link to="/analyze" className="text-muted-foreground hover:text-foreground transition-colors text-sm">Analyze</Link>
          <button onClick={handleAboutClick} className="text-muted-foreground hover:text-foreground transition-colors text-sm">About</button>
          <Button variant="hero" size="sm" asChild>
            <Link to="/analyze">Get Started</Link>
          </Button>
        </div>

        <button className="md:hidden text-foreground" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden glass-card-strong border-t border-border/50 p-4 flex flex-col gap-3">
          <Link to="/" className="text-muted-foreground hover:text-foreground py-2" onClick={() => setMobileOpen(false)}>Home</Link>
          <Link to="/analyze" className="text-muted-foreground hover:text-foreground py-2" onClick={() => setMobileOpen(false)}>Analyze</Link>
          <button onClick={handleAboutClick} className="text-left text-muted-foreground hover:text-foreground py-2">About</button>
          <Button variant="hero" size="sm" asChild>
            <Link to="/analyze" onClick={() => setMobileOpen(false)}>Get Started</Link>
          </Button>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
