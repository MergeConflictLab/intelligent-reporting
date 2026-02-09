export const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
export const SIDECAR_BASE_URL = process.env.NEXT_PUBLIC_SIDECAR_URL || "http://localhost:8001/api";

async function fetchWithRetry(url: string, options: RequestInit, retries = 3, backoff = 1000): Promise<any> {
    try {
        const res = await fetch(url, options);

        if (res.ok) {
            return res.json();
        }

        if (res.status === 429 || res.status >= 500) {
            if (retries > 0) {
                console.warn(`Request failed with status ${res.status}. Retrying in ${backoff}ms...`);
                await new Promise(resolve => setTimeout(resolve, backoff));
                return fetchWithRetry(url, options, retries - 1, backoff * 2);
            }
        }

        throw new Error(`Request failed with status: ${res.status}`);
    } catch (error) {
        if (retries > 0 && error instanceof TypeError) { // Network errors or CORS issues often manifest as TypeError
             console.warn(`Network error: ${error}. Retrying in ${backoff}ms...`);
             await new Promise(resolve => setTimeout(resolve, backoff));
             return fetchWithRetry(url, options, retries - 1, backoff * 2);
        }
        throw error;
    }
}

export async function uploadFile(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    
    return fetchWithRetry(`${SIDECAR_BASE_URL}/upload`, {
        method: "POST",
        body: formData
    });
}

export async function profileData(filePath: string) {
    console.log("[DEBUG] Profiling file:", filePath);
    const res = await fetchWithRetry(`${SIDECAR_BASE_URL}/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath })
    });
    console.log("[DEBUG] Profile Result:", JSON.stringify(res, null, 2));
    return res;
}

export async function runSupervisor(profileData: any, metadataRes: any, offlineMode: boolean = false) {
    console.log("[DEBUG] Running Supervisor with:", { 
        schema_sample: profileData.schema_info,
        metadata_cols: metadataRes.columns || metadataRes.supervisor_description 
    });
    return fetchWithRetry(`${BACKEND_BASE_URL}/agents/supervisor/run`, { 
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            sample_data: profileData.sample_data,
            description: metadataRes.columns || metadataRes.supervisor_description || [], // Corrected: Backend returns columns directly, Sidecar wrapped it
            offline_mode: offlineMode
        }) 
    });
}

export async function executeTask(task: any, fileName: string, profileData: any, offlineMode: boolean = false) {
    console.log("[DEBUG] Executing Task:", task.name);
    return fetchWithRetry(`${SIDECAR_BASE_URL}/execute_task`, {
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            task: task,
            sandbox_data_path: "/sandbox/data/" + fileName, 
            sample_data: profileData.sample_data,
            description: profileData.description,
            schema_info: profileData.schema_info,
            offline_mode: offlineMode
        })
    });
}

export async function getMetadata(profileData: any, offlineMode: boolean = false) {
    console.log("[DEBUG] Fetching Metadata with schema:", profileData.schema_info);
    const res = await fetchWithRetry(`${BACKEND_BASE_URL}/agents/metadata/run`, { 
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            sample_data: profileData.sample_data,
            description: profileData.description,
            schema_info: profileData.schema_info,
            offline_mode: offlineMode
        }) 
    });

    console.log("[DEBUG] Raw Metadata Response:", JSON.stringify(res, null, 2));

    // Fix: Backend returns { columns: [...] }, Frontend expects { supervisor_description: [...] }
    if (res.columns && !res.supervisor_description) {
        console.log("[DEBUG] Mapping columns to supervisor_description");
        res.supervisor_description = res.columns;
    }
    return res;
}
