export type GenerateContentInput = {
  modelId: string;
  prompt: string;
};

export async function generateContentStub(input: GenerateContentInput): Promise<string> {
  await new Promise((resolve) => setTimeout(resolve, 350));
  if (!input.prompt.trim()) {
    return "Enter a prompt to generate content. The LLM engine is not wired yet—this is a UI shell.";
  }
  return `Stub response for model "${input.modelId || "default"}": ${input.prompt.slice(0, 140)}${input.prompt.length > 140 ? "…" : ""}`;
}
