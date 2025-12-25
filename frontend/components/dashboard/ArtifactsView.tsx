import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, CheckCircle2 } from "lucide-react";

interface ArtifactsViewProps {
    artifacts: any[];
}

export function ArtifactsView({ artifacts }: ArtifactsViewProps) {
    return (
        <div className="space-y-6">
          {artifacts.length === 0 && (
              <div className="text-center text-muted-foreground py-10">Waiting for agents to generate artifacts...</div>
          )}
          {artifacts.map((art, i) => (
            <Card key={i} className="bg-card border-border border-l-4 border-l-primary">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-mono flex items-center">
                  <FileText className="mr-2 h-4 w-4 text-primary" /> 
                  <span className="text-primary">{art.filename}</span>
                </CardTitle>
                <Badge variant="outline" className="text-secondary border-secondary bg-secondary/10">Verified Insight</Badge>
              </CardHeader>
              <CardContent className="space-y-4">
                {art.content && (
                    <div className="aspect-video bg-muted rounded-lg flex items-center justify-center border border-border overflow-hidden">
                      <img src={`data:image/png;base64,${art.content}`} alt={art.filename} className="max-h-full" />
                    </div>
                )}
                
                <div className="space-y-3 pt-2">
                    {/* Observation */}
                    {art.insight.observation && (
                        <div className="bg-muted p-3 rounded-md border border-border">
                            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Observation</h4>
                            <p className="text-foreground text-sm leading-relaxed">{art.insight.observation}</p>
                        </div>
                    )}

                    {/* Insight */}
                    {art.insight.insight && (
                        <div className="bg-secondary/10 p-3 rounded-md border border-secondary/30">
                            <h4 className="text-xs font-semibold text-primary uppercase tracking-wider mb-1">Key Insight</h4>
                            <p className="text-foreground text-sm leading-relaxed font-medium">{art.insight.insight}</p>
                        </div>
                    )}

                    {/* Actionable */}
                    {art.insight.actionable && Array.isArray(art.insight.actionable) && (
                        <div className="bg-primary/10 p-3 rounded-md border border-primary/30">
                            <h4 className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Recommended Actions</h4>
                            <ul className="space-y-2">
                                {art.insight.actionable.map((action: string, idx: number) => (
                                    <li key={idx} className="flex items-start text-sm text-foreground">
                                        <CheckCircle2 className="h-4 w-4 text-secondary mr-2 mt-0.5 shrink-0" />
                                        <span>{action}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                    
                    {/* Fallback for raw string or unknown structure */}
                    {!art.insight.observation && !art.insight.insight && !art.insight.actionable && (
                        <p className="text-muted-foreground text-sm">{JSON.stringify(art.insight)}</p>
                    )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
    );
}
