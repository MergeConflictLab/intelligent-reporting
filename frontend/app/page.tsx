"use client";
import { useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { PipelineStep } from "@/components/dashboard/PipelineStep";
import { UploadView } from "@/components/dashboard/UploadView";
import { ProfileView } from "@/components/dashboard/ProfileView";
import { MetadataView } from "@/components/dashboard/MetadataView";
import { ExecutionPlanView } from "@/components/dashboard/ExecutionPlanView";
import { ArtifactsView } from "@/components/dashboard/ArtifactsView";
import { 
    uploadFile, 
    profileData, 
    getMetadata, 
    runSupervisor, 
    executeTask 
} from "./utils/api";
import { downloadReport } from "./utils/exportUtils";

export default function Dashboard() {
  const [stage, setStage] = useState(0); // 0: Idle, 1: Profiling, 2: Metadata, 3: Supervisor, 4: Results
  const [viewState, setViewState] = useState(0); // View control
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Intermediate Results State
  const [profileResult, setProfileResult] = useState<any>(null);
  const [metadataResult, setMetadataResult] = useState<any>(null);
  const [supervisorResult, setSupervisorResult] = useState<any>(null);

  const handleExport = () => {
      downloadReport(artifacts, "analysis_report.md");
  };

  const runPipeline = async () => {
    if (!selectedFile) {
      alert("Please select a file first.");
      return;
    }

    setIsProcessing(true);

    // Reset results
    setProfileResult(null);
    setMetadataResult(null);
    setSupervisorResult(null);
    setArtifacts([]);
    setViewState(1); // Auto-switch to Profiling view on start

    try {
        // Stage 0: Upload
        const uploadRes = await uploadFile(selectedFile);
        const filePath = uploadRes.file_path; 

        // Stage 1: Profiling
        setStage(1);
        const profileRes = await profileData(filePath);
        setProfileResult(profileRes);
        setViewState(2); 
        
        // Stage 2: Metadata
        setStage(2);
        const metadataRes = await getMetadata(profileRes);
        setMetadataResult(metadataRes);
        setViewState(3); 

        // Stage 3: Supervisor
        setStage(3);
        const supervisorRes = await runSupervisor(profileRes, metadataRes);
        setSupervisorResult(supervisorRes);
        setViewState(4); 

        // Stage 4: Execution
        setStage(4);
        const newArtifacts = [];
        const tasks = supervisorRes.tasks || [];
        
        for (const task of tasks) {
            try {
                const execRes = await executeTask(task, selectedFile.name, profileRes);

                // Add artifacts
                if (execRes.artifacts && execRes.artifacts.length > 0) {
                     for (const art of execRes.artifacts) {
                        newArtifacts.push({
                            filename: art.filename,
                            content: art.content_base64, 
                            insight: execRes.insights ? execRes.insights : { observation: "Analysis complete." } 
                        });
                     }
                } else if (execRes.stdout) {
                     newArtifacts.push({
                        filename: `Output: ${execRes.task_name}`,
                        content: null, 
                        insight: { observation: execRes.stdout }
                     });
                }
                
                setArtifacts([...newArtifacts]); // Update state incrementally
            } catch (e) {
                console.error("Task failed", task, e);
            }
        }
    } catch (error) {
        console.error("Pipeline failed", error);
        alert("Pipeline failed. See console.");
        setStage(0); 
    } finally {
        setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground font-sans">
      <Header 
        onFileSelect={setSelectedFile} 
        onRun={runPipeline} 
        onExport={handleExport}
        selectedFile={selectedFile} 
        isProcessing={isProcessing}
        stage={stage} 
        artifactsCount={artifacts.length}
      />
      
      <main className="flex-1 flex flex-col md:grid md:grid-cols-12 gap-4 md:gap-6 p-4 md:p-6 overflow-hidden">
        {/* Sidebar: Pipeline Status */}
        <div className="md:col-span-3 flex md:flex-col overflow-x-auto md:overflow-x-visible gap-3 md:gap-4 pb-2 md:pb-0 shrink-0 scrollbar-hide">
            <PipelineStep 
                label="Data Upload" 
                active={viewState === 0} 
                done={!!selectedFile} 
                onClick={() => setViewState(0)}
            />
            <PipelineStep 
                label="Data Profiling" 
                active={viewState === 1} 
                done={stage > 1} 
                onClick={() => setViewState(1)}
                disabled={stage < 1}
            />
            <PipelineStep 
                label="Metadata Extraction" 
                active={viewState === 2} 
                done={stage > 2} 
                onClick={() => setViewState(2)}
                disabled={stage < 2}
            />
            <PipelineStep 
                label="Task Planning" 
                active={viewState === 3} 
                done={stage > 3} 
                onClick={() => setViewState(3)}
                disabled={stage < 3}
            />
            <PipelineStep 
                label="Agent Execution" 
                active={viewState === 4} 
                done={stage === 4 || (stage === 4 && artifacts.length > 0)} 
                onClick={() => setViewState(4)}
                disabled={stage < 4}
            />
        </div>

        {/* Main Content Area */}
        <div className="md:col-span-9 overflow-y-auto space-y-4 md:space-y-6 md:pr-2 pb-20 md:pb-0">
            
            {viewState === 0 && <UploadView selectedFile={selectedFile} />}

            {viewState === 1 && <ProfileView profileResult={profileResult} />}

            {viewState === 2 && <MetadataView metadataResult={metadataResult} />}

            {viewState === 3 && <ExecutionPlanView supervisorResult={supervisorResult} />}

            {viewState === 4 && <ArtifactsView artifacts={artifacts} />}
            
        </div>
      </main>
    </div>
  );
}