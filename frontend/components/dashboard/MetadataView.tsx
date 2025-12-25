import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { List } from "lucide-react";

interface MetadataViewProps {
    metadataResult: any;
}

export function MetadataView({ metadataResult }: MetadataViewProps) {
    if (!metadataResult) return null;

    return (
        <div className="space-y-4">
            <h2 className="text-lg font-semibold text-primary flex items-center"><List className="mr-2 h-5 w-5" /> Semantic Metadata</h2>
            <div className="grid gap-3">
                {Array.isArray(metadataResult.supervisor_description) ? (
                    metadataResult.supervisor_description.map((col: any, i: number) => (
                        <Card key={i} className="bg-card border-border hover:border-primary transition-colors">
                            <CardContent className="p-4 flex flex-col gap-2">
                                <div className="flex items-center justify-between">
                                    <span className="font-mono text-primary font-semibold">{col.name || `Column ${i+1}`}</span>
                                    {col.type && (
                                        <Badge variant="outline" className="text-muted-foreground border-border bg-muted">
                                            {col.type}
                                        </Badge>
                                    )}
                                </div>
                                <p className="text-sm text-foreground">
                                    {col.description || col.summary || JSON.stringify(col)}
                                </p>
                            </CardContent>
                        </Card>
                    ))
                ) : (
                    <Card className="bg-card border-border">
                        <CardContent className="p-4">
                            <pre className="text-xs text-foreground whitespace-pre-wrap">{JSON.stringify(metadataResult.supervisor_description, null, 2)}</pre>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
