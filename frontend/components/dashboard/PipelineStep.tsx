import { Loader2, CheckCircle2 } from "lucide-react";

interface PipelineStepProps {
    label: string; 
    active: boolean; 
    done: boolean;
    onClick?: () => void;
    disabled?: boolean;
}

export function PipelineStep({ 
    label, 
    active, 
    done, 
    onClick,
    disabled 
}: PipelineStepProps) {
  return (
    <div 
        onClick={!disabled ? onClick : undefined}
        className={`p-4 rounded-lg border transition-all cursor-pointer ${
            active ? 'bg-card border-primary shadow-[0_0_15px_rgba(139,174,102,0.1)]' : 
            disabled ? 'bg-muted border-border opacity-50 cursor-not-allowed' :
            'bg-card/50 border-border hover:border-primary/50'
        }`}
    >
      <div className="flex items-center justify-between">
        <span className={`text-sm font-medium ${active ? 'text-primary' : 'text-muted-foreground'}`}>{label}</span>
        {done ? <CheckCircle2 className="h-4 w-4 text-secondary" /> : active ? <Loader2 className="h-4 w-4 animate-spin text-primary" /> : null}
      </div>
    </div>
  );
}
