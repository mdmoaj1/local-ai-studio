import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { publicEnv } from "@/lib/env";

export default function SettingsPage() {
  return (
    <div className="grid gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Environment</CardTitle>
          <CardDescription>Frontend reads public configuration at build/runtime.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm">
          <div className="flex flex-col gap-1 rounded-lg border border-border bg-background/40 p-3">
            <div className="text-xs text-muted-foreground">NEXT_PUBLIC_APP_MODE</div>
            <div className="font-mono text-xs">{publicEnv.appMode}</div>
          </div>
          <div className="flex flex-col gap-1 rounded-lg border border-border bg-background/40 p-3">
            <div className="text-xs text-muted-foreground">Resolved API base</div>
            <div className="font-mono text-xs">{publicEnv.apiBaseUrl}</div>
          </div>
          <Separator />
          <div className="text-muted-foreground">
            <span className="font-mono">web</span>: set <span className="font-mono">NEXT_PUBLIC_API_URL</span>.{" "}
            <span className="font-mono">desktop</span>: uses <span className="font-mono">127.0.0.1</span> and optional{" "}
            <span className="font-mono">NEXT_PUBLIC_API_PORT</span>.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
