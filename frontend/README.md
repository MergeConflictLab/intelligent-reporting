# Intelligent Reporting Frontend

This is a [Next.js](https://nextjs.org) project built with React and Tailwind CSS. It serves as the interactive dashboard for the Intelligent Reporting platform, allowing users to upload datasets, visualize automated insights, and orchestrate AI-driven analysis.

## Overview

The frontend interacts with the backend API to drive a multi-stage analysis pipeline:
1. **Data Upload**: Send CSV/tabular data to the backend.
2. **Profiling**: View statistical summaries and automated data checks.
3. **Metadata Extraction**: Review AI-inferred column meanings.
4. **Planning**: See the Supervisor Agent's proposed analysis tasks.
5. **Execution**: Watch as agents generate code, create charts, and derive insights in real-time.

## Getting Started

### Prerequisites

- Node.js 18+
- npm, yarn, pnpm, or bun

### Installation

1. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Architecture

### Directory Structure

- **`app/`**: App Router logic.
    - `page.tsx`: Main dashboard controller.
    - `utils/api.ts`: API client.
- **`components/dashboard/`**: Pipeline-specific components.
    - `UploadView.tsx`, `ProfileView.tsx`, etc.
- **`components/ui/`**: Reusable UI atoms (based on shadcn/ui patterns).

### Key Technologies

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **Lucide React** (Icons)

## Configuration

The application expects the backend to be running on `http://localhost:8000`. You can configure this in `app/utils/api.ts` or via environment variables (future improvement).

## Roadmap

- [ ] **Interactive Visualizations**: Replace static images with interactive charts (Recharts/Visx).
- [ ] **History & Sessions**: Save and resume past analysis sessions.
- [ ] **Export**: Export full reports to PDF or Markdown.
- [ ] **Toast Notifications**: Improved error feedback.
