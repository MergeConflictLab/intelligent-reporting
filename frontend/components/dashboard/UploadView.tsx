import { Badge } from "@/components/ui/badge";

interface UploadViewProps {
    selectedFile: File | null;
}

export function UploadView({ selectedFile }: UploadViewProps) {
    return (
        <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground border-2 border-dashed border-border rounded-xl space-y-4">
            <p>Upload a CSV file to begin analysis.</p>
            {selectedFile && <Badge variant="secondary" className="text-lg px-4 py-2 bg-secondary text-secondary-foreground">{selectedFile.name}</Badge>}
        </div>
    );
}
