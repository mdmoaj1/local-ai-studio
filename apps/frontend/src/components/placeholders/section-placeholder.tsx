import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type SectionPlaceholderProps = {
  title: string;
  description: string;
};

export function SectionPlaceholder({ title, description }: SectionPlaceholderProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">
        This module is scaffolded for the next milestone. The layout, routing, and API surface are already in place.
      </CardContent>
    </Card>
  );
}
