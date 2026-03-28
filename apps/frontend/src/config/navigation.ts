import {
  Boxes,
  Database,
  GraduationCap,
  History,
  Layers,
  LayoutDashboard,
  Mic2,
  Puzzle,
  Settings,
  Sparkles,
  Volume2,
} from "lucide-react";

export type NavItem = {
  title: string;
  href: string;
  icon: typeof LayoutDashboard;
};

export const mainNav: NavItem[] = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { title: "Content Generator", href: "/content-generator", icon: Sparkles },
  { title: "TTS", href: "/tts", icon: Volume2 },
  { title: "Voice Cloning", href: "/voice-cloning", icon: Mic2 },
  { title: "Models", href: "/models", icon: Boxes },
  { title: "Datasets", href: "/datasets", icon: Database },
  { title: "Finetune", href: "/finetune", icon: GraduationCap },
  { title: "Adapters", href: "/adapters", icon: Layers },
  { title: "Plugins", href: "/plugins", icon: Puzzle },
  { title: "History", href: "/history", icon: History },
  { title: "Settings", href: "/settings", icon: Settings },
];
