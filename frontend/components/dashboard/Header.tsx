import { Button } from "@/components/ui/button";
import { Loader2, Play, Download } from "lucide-react";
import Image from "next/image";

interface HeaderProps {
    onFileSelect: (file: File | null) => void;
    onRun: () => void;
    onExport: () => void;
    selectedFile: File | null;
    stage: number;
    artifactsCount: number;
    isProcessing: boolean;
}

export function Header({ onFileSelect, onRun, onExport, selectedFile, isProcessing, artifactsCount }: HeaderProps) {
    return (
        <header className="border-b border-border p-4 flex flex-col md:flex-row justify-between items-center gap-4 bg-card/50 backdrop-blur-md sticky top-0 z-50">
            <h1 className="text-xl flex sm:justify-between justify-center font-bold tracking-tight text-primary w-full md:w-auto md:text-left flex items-center justify-center md:justify-between gap-2">
                <Image src="/growth.png" alt="growth" width={24} height={24} className="inline-block"/>
                <span className="text-primary">Intelligent Reporting</span>
            </h1>
            <div className="flex flex-col md:flex-row items-center gap-4 w-full md:w-auto">
                <input 
                    type="file" 
                    onChange={(e) => onFileSelect(e.target.files ? e.target.files[0] : null)} 
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

                <Button onClick={onRun} disabled={!selectedFile || isProcessing} className="bg-primary text-primary-foreground hover:bg-primary/90 w-full md:w-auto">
                {isProcessing ? <Loader2 className="mr-2 animate-spin" /> : <Play className="mr-2" />}
                Run Analysis
                </Button>
            </div>
        </header>
    );
}
