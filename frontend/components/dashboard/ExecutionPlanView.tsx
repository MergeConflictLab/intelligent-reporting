import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Cpu } from "lucide-react";

interface ExecutionPlanViewProps {
    supervisorResult: any;
}

export function ExecutionPlanView({ supervisorResult }: ExecutionPlanViewProps) {
    if (!supervisorResult) return null;

    return (
        <div className="space-y-4">
            <h2 className="text-lg font-semibold text-primary flex items-center"><Cpu className="mr-2 h-5 w-5" /> Execution Plan</h2>
            <div className="grid gap-4">
                {supervisorResult.tasks.map((task: any, i: number) => (
                     <Card key={i} className="bg-card border-border">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-mono text-foreground">{i + 1}. {task.name}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-xs text-muted-foreground">{task.description}</p>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
}
