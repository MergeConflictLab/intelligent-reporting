import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Loader2, Play, Download, WifiOff } from "lucide-react";
import Image from "next/image";

interface HeaderProps {
  onFileSelect: (file: File | null) => void;
  onRun: () => void;
  onExport: () => void;
  selectedFile: File | null;
  stage: number;
  artifactsCount: number;
  isProcessing: boolean;
  offlineMode: boolean;
  onToggleOffline: (checked: boolean) => void;
}

export function Header({
  onFileSelect,
  onRun,
  onExport,
  selectedFile,
  isProcessing,
  artifactsCount,
  offlineMode,
  onToggleOffline,
}: HeaderProps) {
  return (
    <header className="border-b border-border p-4 flex flex-col gap-4 bg-card/50 backdrop-blur-md sticky top-0 z-50">
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <h1 className="text-xl flex sm:justify-between justify-center font-bold tracking-tight text-primary w-full md:w-auto md:text-left flex items-center justify-center md:justify-between gap-2">
          <Image
            src="/growth.png"
            alt="growth"
            width={24}
            height={24}
            className="inline-block"
          />
          <span className="text-primary">Intelligent Reporting</span>
        </h1>

        <div className="flex flex-col md:flex-row items-center gap-4 w-full md:w-auto">
          <div className="flex items-center gap-2 px-3 py-2 bg-secondary/50 rounded-full border border-border">
            <span className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <WifiOff className="w-4 h-4" /> Offline Mode
            </span>
            <Switch
              checked={offlineMode}
              onCheckedChange={onToggleOffline}
              disabled={isProcessing}
            />
          </div>

          <input
            type="file"
            onChange={(e) =>
              onFileSelect(e.target.files ? e.target.files[0] : null)
            }
            className="text-sm text-muted-foreground w-full md:w-auto
                        file:mr-4 file:py-2 file:px-4
                        file:rounded-full file:border-0
                        file:text-sm file:font-semibold
                        file:bg-secondary file:text-secondary-foreground
                        hover:file:bg-secondary/80
                        "
          />

          <Button
            variant="outline"
            onClick={onExport}
            disabled={artifactsCount === 0 || isProcessing}
            className="w-full md:w-auto border-primary/20 hover:bg-primary/5"
          >
            <Download className="mr-2 h-4 w-4" /> Export Report
          </Button>

          <Button
            onClick={onRun}
            disabled={!selectedFile || isProcessing}
            className="bg-primary text-primary-foreground hover:bg-primary/90 w-full md:w-auto"
          >
            {isProcessing ? (
              <Loader2 className="mr-2 animate-spin" />
            ) : (
              <Play className="mr-2" />
            )}
            Run Analysis
          </Button>
        </div>
      </div>

      {offlineMode && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 text-yellow-600 dark:text-yellow-400 px-4 py-2 rounded-md text-sm text-center animate-in fade-in slide-in-from-top-1">
          ⚠️ <strong>Offline Mode Active:</strong> Analysis runs locally on your
          CPU. This handles sensitive data securely but is significantly slower
          (up to 10 mins).
        </div>
      )}
    </header>
  );
}
