"use client";

import { ContentGeneratorView } from "@/components/content-generator/content-generator-view";
import { useContentGenerator } from "@/hooks/use-content-generator";

export function ContentGeneratorContainer() {
  const g = useContentGenerator();

  return (
    <ContentGeneratorView
      installedModels={g.installedModels}
      enabledPlugins={g.enabledPlugins}
      modelId={g.modelId}
      onModelIdChange={g.setModelId}
      pluginId={g.pluginId}
      onPluginIdChange={g.setPluginId}
      maxTokens={g.maxTokens}
      onMaxTokensChange={g.setMaxTokens}
      prompt={g.prompt}
      onPromptChange={g.setPrompt}
      result={g.result}
      streaming={g.streaming}
      streamError={g.streamError}
      onStream={() => void g.runStream()}
      stubMutation={g.stubMutation}
      onClear={() => g.setResult("")}
    />
  );
}
