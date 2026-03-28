"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { mainNav } from "@/config/navigation";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-[260px] shrink-0 flex-col border-r border-border bg-card/40 backdrop-blur">
      <div className="flex items-center gap-2 px-4 py-4">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-primary/15 text-primary">
          <span className="font-mono text-xs font-bold">LA</span>
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold tracking-tight">Local AI Studio</div>
          <div className="text-xs text-muted-foreground">Desktop-class workspace</div>
        </div>
      </div>
      <Separator />
      <ScrollArea className="flex-1 px-2 py-3">
        <nav className="flex flex-col gap-1">
          {mainNav.map((item) => {
            const active = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-accent text-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                )}
              >
                <Icon className="h-4 w-4 shrink-0 opacity-90" />
                <span className="truncate">{item.title}</span>
              </Link>
            );
          })}
        </nav>
      </ScrollArea>
      <Separator />
      <div className="px-4 py-3 text-xs text-muted-foreground">
        Engine layer is isolated for future desktop packaging.
      </div>
    </aside>
  );
}
