export const API_BASE_URL = "http://localhost:8000/api";

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
    
    return fetchWithRetry(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData
    });
}

export async function profileData(filePath: string) {
    return fetchWithRetry(`${API_BASE_URL}/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath })
    });
}

export async function getMetadata(profileData: any) {
    return fetchWithRetry(`${API_BASE_URL}/metadata`, { 
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            sample_data: profileData.sample_data,
            description: profileData.description,
            schema_info: profileData.schema_info
        }) 
    });
}

export async function runSupervisor(profileData: any, metadataRes: any) {
    return fetchWithRetry(`${API_BASE_URL}/supervisor`, { 
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            sample_data: profileData.sample_data,
            supervisor_description: metadataRes.supervisor_description
        }) 
    });
}

export async function executeTask(task: any, fileName: string, profileData: any) {
    return fetchWithRetry(`${API_BASE_URL}/execute_task`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            task: task,
            sandbox_data_path: "/sandbox/data/" + fileName, 
            sample_data: profileData.sample_data,
            description: profileData.description,
            schema_info: profileData.schema_info
        })
    });
}
