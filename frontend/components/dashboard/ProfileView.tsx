import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Database } from "lucide-react";

interface ProfileViewProps {
    profileResult: any;
}

export function ProfileView({ profileResult }: ProfileViewProps) {
    if (!profileResult) return null;

    return (
        <div className="space-y-4">
            <h2 className="text-lg font-semibold text-primary flex items-center"><Database className="mr-2 h-5 w-5" /> Data Profile</h2>
            
            <Card className="bg-card border-border">
                <CardHeader><CardTitle className="text-sm">Summary Statistics</CardTitle></CardHeader>
                <CardContent className="p-4">
                     {typeof profileResult.description === 'object' && !Array.isArray(profileResult.description) ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.entries(profileResult.description).map(([key, value]) => (
                                <div key={key} className="bg-muted p-3 rounded border border-border">
                                    <div className="text-muted-foreground text-xs uppercase tracking-wider mb-1">{key}</div>
                                    <div className="text-foreground font-mono text-sm break-all">
                                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                    </div>
                                </div>
                            ))}
                        </div>
                     ) : (
                        <pre className="text-xs text-foreground whitespace-pre-wrap">{JSON.stringify(profileResult.description, null, 2)}</pre>
                     )}
                </CardContent>
            </Card>

             <Card className="bg-card border-border">
                 <CardHeader><CardTitle className="text-sm">Schema Info</CardTitle></CardHeader>
                <CardContent className="p-0">
                    <div className="border-t border-border">
                        {Object.entries(profileResult.schema_info || {}).map(([col, type], i) => (
                            <div key={i} className="flex items-center justify-between p-3 border-b border-border last:border-0 hover:bg-muted/50">
                                <span className="text-sm font-medium text-foreground">{col}</span>
                                <Badge variant="secondary" className="bg-secondary text-secondary-foreground font-mono text-xs hover:bg-secondary/80">{String(type)}</Badge>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
