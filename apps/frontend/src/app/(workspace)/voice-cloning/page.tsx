"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Mic2,
  Upload,
  Trash2,
  Clock,
  Loader2,
  AlertCircle,
  Volume2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  deleteVoice,
  listVoices,
  uploadVoice,
  type Voice,
} from "@/services/tts-api";

export default function VoicesPage() {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);

  // Upload state
  const [uploadName, setUploadName] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Deletion
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Drag-over state
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // -------------------------------------------------------------------
  // Load
  // -------------------------------------------------------------------
  async function reload() {
    try {
      const vs = await listVoices();
      setVoices(vs);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void reload();
  }, []);

  // -------------------------------------------------------------------
  // Upload
  // -------------------------------------------------------------------
  const handleUpload = useCallback(async () => {
    if (!uploadFile || !uploadName.trim()) return;
    setUploading(true);
    setUploadError(null);
    try {
      await uploadVoice(uploadName.trim(), uploadFile);
      setUploadName("");
      setUploadFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await reload();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, [uploadFile, uploadName]);

  // -------------------------------------------------------------------
  // Delete
  // -------------------------------------------------------------------
  async function handleDelete(id: number) {
    setDeletingId(id);
    try {
      await deleteVoice(id);
      setVoices((prev) => prev.filter((v) => v.id !== id));
    } catch {
      // silently ignore; could show toast
    } finally {
      setDeletingId(null);
    }
  }

  // -------------------------------------------------------------------
  // Drag-and-drop
  // -------------------------------------------------------------------
  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) setUploadFile(file);
  }

  function formatDuration(sec: number): string {
    if (sec < 60) return `${sec.toFixed(1)}s`;
    const m = Math.floor(sec / 60);
    const s = Math.round(sec % 60);
    return `${m}m ${s}s`;
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-primary/10">
          <Volume2 className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Voice Library</h1>
          <p className="text-sm text-muted-foreground">
            Upload reference audio samples to clone speaker voices for TTS generation.
          </p>
        </div>
      </div>

      {/* Upload card */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Upload New Voice
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {/* Drag-and-drop area */}
          <div
            id="voice-drop-zone"
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`
              relative flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed
              p-8 cursor-pointer transition-colors select-none
              ${dragOver ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-accent/30"}
            `}
          >
            <Mic2 className="h-8 w-8 text-muted-foreground" />
            {uploadFile ? (
              <div className="text-center">
                <p className="text-sm font-medium">{uploadFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(uploadFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-sm font-medium">Drop audio here or click to browse</p>
                <p className="text-xs text-muted-foreground">WAV, MP3, FLAC, OGG accepted</p>
              </div>
            )}
            <input
              ref={fileInputRef}
              id="voice-file-input"
              type="file"
              accept=".wav,.mp3,.flac,.ogg,audio/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) setUploadFile(file);
              }}
            />
          </div>

          {/* Name input + submit */}
          <div className="flex gap-3">
            <div className="flex-1">
              <Label htmlFor="voice-name-input" className="sr-only">Voice name</Label>
              <Input
                id="voice-name-input"
                placeholder="Voice name (e.g. narrator-en)"
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") void handleUpload(); }}
              />
            </div>
            <Button
              id="voice-upload-btn"
              onClick={() => void handleUpload()}
              disabled={!uploadFile || !uploadName.trim() || uploading}
              className="gap-2 shrink-0"
            >
              {uploading ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Uploading…</>
              ) : (
                <><Upload className="h-4 w-4" /> Upload</>
              )}
            </Button>
          </div>

          {uploadError && (
            <div className="flex items-center gap-2 text-destructive text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {uploadError}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Voice list */}
      <div>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Registered Voices ({loading ? "…" : voices.length})
        </h2>

        {loading ? (
          <div className="flex items-center gap-2 text-muted-foreground text-sm p-4">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading voices…
          </div>
        ) : voices.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
              <Volume2 className="h-8 w-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                No voices yet — upload a WAV or MP3 above to get started.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {voices.map((voice) => (
              <Card key={voice.id} className="group relative overflow-hidden">
                <CardContent className="p-4 flex items-center gap-3">
                  {/* Icon */}
                  <div className="p-2 rounded-lg bg-primary/10 shrink-0">
                    <Mic2 className="h-5 w-5 text-primary" />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{voice.name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Clock className="h-3 w-3 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">
                        {formatDuration(voice.duration)}
                      </span>
                      <Badge variant="secondary" className="text-xs">
                        #{voice.id}
                      </Badge>
                    </div>
                  </div>

                  {/* Delete */}
                  <Button
                    id={`voice-delete-btn-${voice.id}`}
                    variant="ghost"
                    size="icon"
                    className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
                    onClick={() => void handleDelete(voice.id)}
                    disabled={deletingId === voice.id}
                    aria-label={`Delete voice ${voice.name}`}
                  >
                    {deletingId === voice.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
