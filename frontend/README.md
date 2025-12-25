# Intelligent Reporting Frontend

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Overview
The Intelligent Reporting frontend is a React-based dashboard built with Next.js 14 and Tailwind CSS. It provides a user interface for uploading data files, profiling them, extracting metadata, planning analysis tasks via an AI Supervisor, and executing those tasks to generate insights and visualizations.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Architecture

### Directory Structure
- **`app/`**: Contains the main application logic and routing (App Router).
    - `page.tsx`: The main dashboard controller. Manages global state (stage, viewState) and orchestrates the pipeline.
    - `layout.tsx`: Root layout definition.
    - `utils/api.ts`: Centralized API client for communicating with the backend (running on localhost:8000).
- **`components/dashboard/`**: Domain-specific components for the reporting pipeline.
    - `Header.tsx`: Top navigation and file selection.
    - `PipelineStep.tsx`: Sidebar navigation items representing pipeline stages.
    - `UploadView.tsx`, `ProfileView.tsx`, `MetadataView.tsx`, `ExecutionPlanView.tsx`, `ArtifactsView.tsx`: Specialized views for each stage of the pipeline.
- **`components/ui/`**: Reusable UI atoms (cards, badges, buttons).

### Key Technologies
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **Lucide React** (Icons)

## End-to-End User Flow

The application follows a linear data processing pipeline:

1.  **Data Upload (`Stage 0`)**:
    -   User selects a CSV file.
    -   File is uploaded to the backend via `/api/upload`.
    -   **View**: `UploadView`

2.  **Data Profiling (`Stage 1`)**:
    -   Backend analyzes the file (rows, columns, data types, missing values).
    -   **View**: `ProfileView` displays the summary statistics.

3.  **Metadata Extraction (`Stage 2`)**:
    -   AI analyzes the profile to understand the semantic meaning of columns.
    -   **View**: `MetadataView` shows the inferred schema information.

4.  **Task Planning (`Stage 3`)**:
    -   Supervisor Agent proposes a list of analysis tasks based on the data profile and metadata.
    -   **View**: `ExecutionPlanView` lists the proposed tasks (e.g., "Analyze sales trends", "Identify outliers").

5.  **Agent Execution (`Stage 4`)**:
    -   The system iterates through the proposed tasks.
    -   Each task is executed sequentially by the backend agents.
    -   **View**: `ArtifactsView` renders the results in real-time as they arrive.
        -   **Outputs**: Text observations, specific insights, actionable recommendations, and generated plots (base64 images).

## Work in Progress (WIP) & Improvements

### Current Limitations (WIP)
-   **Error Handling**:
    -   Currently relies on `console.error` and native `alert()`.
    -   Specific error states (e.g., API timeout, malformed CSV) are not gracefully handled in the UI.
-   **Type Safety**:
    -   Heavy usage of `any` types (e.g., `artifacts: any[]`, `supervisorResult: any`). Interfaces need to be defined for backend responses.
-   **Configuration**:
    -   API Endpoint is hardcoded to `http://localhost:8000/api`. This should be environment-variable driven.
-   **Performance**:
    -   The pipeline logic in `page.tsx` awaits each step sequentially. Long-running tasks freeze the "active" state without detailed progress feedback.

### Proposed Improvements

#### User Experience (UX)
-   **Loading Skeletons**: Add skeleton loaders for each view instead of full-screen blocking or generic spinners.
-   **Toast Notifications**: Replace `alert()` with a toast library (e.g., `sonner` or `react-hot-toast`) for success/error messages.
-   **Interactive Visualizations**: Instead of rendering static base64 images, use a charting library (Recharts, Visx) to render interactive data client-side where possible.
-   **Progress Indication**: Detailed progress bars for the multi-step execution phase (e.g., "Executing task 2 of 5...").

#### Technical Debt
-   **State Management**: Refactor `page.tsx`'s localized state into a reducer or a lightweight state manager if complexity grows.
-   **API Layer**: Use **React Query** (TanStack Query) for data fetching to handle caching, loading states, and retries.
-   **Strict Typing**: Create a shared `types` package or file to ensure frontend and backend data contracts match.

#### Feature Additions
-   **History/Sessions**: Allow users to browse previous reports.
-   **Export**: functionality to download the generated report as a PDF or Markdown file.
-   **Feedback Loop**: Allow users to edit the "Execution Plan" before the agent starts.
