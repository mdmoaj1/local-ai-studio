"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Mic2, Download, Play, Pause, Waveform, Loader2, AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  audioFileUrl,
  generateSpeech,
  listVoices,
  subscribeTtsProgress,
  type Voice,
} from "@/services/tts-api";
import { apiGetJson } from "@/services/api-client";

interface StudioModel {
  id: number;
  name: string;
  status: string;
  type: string;
}

type GenerateStatus = "idle" | "loading" | "generating" | "done" | "error";

export default function TtsPage() {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [models, setModels] = useState<StudioModel[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  const [selectedVoiceId, setSelectedVoiceId] = useState<string>("");
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [text, setText] = useState("");

  const [status, setStatus] = useState<GenerateStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const wsCleanupRef = useRef<(() => void) | null>(null);

  // -------------------------------------------------------------------
  // Load voices & models
  // -------------------------------------------------------------------
  useEffect(() => {
    async function loadData() {
      try {
        const [vs, ms] = await Promise.all([
          listVoices(),
          apiGetJson<StudioModel[]>("/api/v1/models"),
        ]);
        setVoices(vs);
        setModels(ms.filter((m) => m.status === "installed" && m.type === "tts"));
      } catch {
        // non-fatal — controls will just be empty
      } finally {
        setLoadingData(false);
      }
    }
    void loadData();
  }, []);

  // -------------------------------------------------------------------
  // Cleanup WS on unmount
  // -------------------------------------------------------------------
  useEffect(() => () => wsCleanupRef.current?.(), []);

  // -------------------------------------------------------------------
  // Generate
  // -------------------------------------------------------------------
  const handleGenerate = useCallback(async () => {
    if (!text.trim() || !selectedVoiceId || !selectedModelId) return;

    setStatus("loading");
    setProgress(0);
    setAudioUrl(null);
    setError(null);
    setDuration(null);
    wsCleanupRef.current?.();

    try {
      const res = await generateSpeech({
        text: text.trim(),
        voice_id: Number(selectedVoiceId),
        model_id: Number(selectedModelId),
      });

      setStatus("generating");

      // Subscribe to progress WS
      const cleanup = subscribeTtsProgress(
        res.job_id,
        (pct) => setProgress(pct),
        () => {
          setProgress(100);
          setAudioUrl(audioFileUrl(res.audio_url));
          setDuration(res.duration);
          setStatus("done");
        },
      );
      wsCleanupRef.current = cleanup;

      // Optimistic: set audio as soon as URL is returned
      // (progress events arrive in parallel)
      setAudioUrl(audioFileUrl(res.audio_url));
      setDuration(res.duration);
      setStatus("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
      setStatus("error");
    }
  }, [text, selectedVoiceId, selectedModelId]);

  // -------------------------------------------------------------------
  // Audio player controls
  // -------------------------------------------------------------------
  function handlePlayPause() {
    const el = audioRef.current;
    if (!el) return;
    if (isPlaying) {
      el.pause();
    } else {
      void el.play();
    }
  }

  function handleDownload() {
    if (!audioUrl) return;
    const a = document.createElement("a");
    a.href = audioUrl;
    a.download = `tts-output-${Date.now()}.wav`;
    a.click();
  }

  const canGenerate =
    text.trim().length > 0 &&
    selectedVoiceId !== "" &&
    selectedModelId !== "" &&
    status !== "loading" &&
    status !== "generating";

  return (
    <div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-primary/10">
          <Mic2 className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">TTS Studio</h1>
          <p className="text-sm text-muted-foreground">
            Generate speech from text using your downloaded TTS model and cloned voices.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left — settings */}
        <div className="lg:col-span-1 flex flex-col gap-4">
          {/* Model select */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Model</CardTitle>
            </CardHeader>
            <CardContent>
              <Select
                value={selectedModelId}
                onValueChange={setSelectedModelId}
                disabled={loadingData}
              >
                <SelectTrigger id="tts-model-select">
                  <SelectValue
                    placeholder={loadingData ? "Loading…" : models.length === 0 ? "No TTS models installed" : "Select model"}
                  />
                </SelectTrigger>
                <SelectContent>
                  {models.map((m) => (
                    <SelectItem key={m.id} value={String(m.id)}>
                      {m.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!loadingData && models.length === 0 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Install a TTS model from the Models page first.
                </p>
              )}
            </CardContent>
          </Card>

          {/* Voice select */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Speaker Voice</CardTitle>
            </CardHeader>
            <CardContent>
              <Select
                value={selectedVoiceId}
                onValueChange={setSelectedVoiceId}
                disabled={loadingData}
              >
                <SelectTrigger id="tts-voice-select">
                  <SelectValue
                    placeholder={loadingData ? "Loading…" : voices.length === 0 ? "No voices uploaded" : "Select voice"}
                  />
                </SelectTrigger>
                <SelectContent>
                  {voices.map((v) => (
                    <SelectItem key={v.id} value={String(v.id)}>
                      <div className="flex items-center gap-2">
                        <span>{v.name}</span>
                        <Badge variant="secondary" className="text-xs">
                          {v.duration.toFixed(1)}s
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!loadingData && voices.length === 0 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Upload a voice on the Voices page first.
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right — text + output */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          {/* Text input */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Text to Synthesise</CardTitle>
              <CardDescription>Maximum 4096 characters</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Textarea
                id="tts-text-input"
                placeholder="Type or paste the text you want to convert to speech…"
                className="min-h-[160px] resize-y font-mono text-sm"
                value={text}
                onChange={(e) => setText(e.target.value)}
                maxLength={4096}
              />
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">{text.length} / 4096</span>
                <Button
                  id="tts-generate-btn"
                  onClick={() => void handleGenerate()}
                  disabled={!canGenerate}
                  className="gap-2"
                >
                  {(status === "loading" || status === "generating") ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generating…
                    </>
                  ) : (
                    <>
                      <Mic2 className="h-4 w-4" />
                      Generate Speech
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Progress */}
          {(status === "loading" || status === "generating") && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3 mb-3">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  <span className="text-sm font-medium">
                    {status === "loading" ? "Starting model…" : "Generating audio…"}
                  </span>
                  <span className="ml-auto text-sm text-muted-foreground">{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </CardContent>
            </Card>
          )}

          {/* Error */}
          {status === "error" && error && (
            <Card className="border-destructive/50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm">{error}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Audio player */}
          {audioUrl && status === "done" && (
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Waveform className="h-4 w-4 text-primary" />
                    Generated Audio
                  </CardTitle>
                  {duration !== null && (
                    <Badge variant="secondary">{duration.toFixed(2)}s</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                {/* HTML5 audio element */}
                <audio
                  ref={audioRef}
                  src={audioUrl}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onEnded={() => setIsPlaying(false)}
                  className="w-full"
                  controls
                  id="tts-audio-player"
                />

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    id="tts-play-pause-btn"
                    onClick={handlePlayPause}
                    className="gap-2"
                  >
                    {isPlaying ? (
                      <><Pause className="h-3 w-3" /> Pause</>
                    ) : (
                      <><Play className="h-3 w-3" /> Play</>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    id="tts-download-btn"
                    onClick={handleDownload}
                    className="gap-2"
                  >
                    <Download className="h-3 w-3" />
                    Download WAV
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
