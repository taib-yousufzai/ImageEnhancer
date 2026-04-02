/**
 * API integration layer for image enhancement
 */

export type OutputFormat = 'webp' | 'jpeg' | 'png';

export interface TaskStatus {
  status: 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  estimated_time_remaining?: number | null;
  error?: string;
}

/**
 * Starts an enhancement task
 */
export async function startEnhancement(
  file: File,
  format: OutputFormat = 'webp',
  scale: number = 2,
  width?: number,
  height?: number,
  ultraMode: boolean = false
): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const url = new URL(`${apiUrl}`); // Changed from `${apiUrl}/enhance` to `${apiUrl}`
  url.pathname = '/enhance'; // Added to explicitly set the path
  url.searchParams.append('output_format', format);

  if (width || height) {
    if (width) url.searchParams.append('width', width.toString());
    if (height) url.searchParams.append('height', height.toString());
  } else {
    url.searchParams.append('scale', scale.toString());
  }

  if (ultraMode) {
    url.searchParams.append('ultra_mode', 'true');
  }

  const response = await fetch(url.toString(), {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`Failed to start task: ${errorText}`);
  }

  const data = await response.json();
  return data.task_id;
}

export interface BatchResponse {
  tasks: { filename: string; task_id: string }[];
  errors: { filename: string; error: string }[];
}

/**
 * Starts batch enhancement tasks
 */
export async function startBatchEnhancement(
  files: File[],
  format: OutputFormat = 'webp',
  scale: number = 2,
  width?: number,
  height?: number,
  ultraMode: boolean = false
): Promise<BatchResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const url = new URL(`${apiUrl}`);
  url.pathname = '/enhance-batch';
  url.searchParams.append('output_format', format);

  if (width || height) {
    if (width) url.searchParams.append('width', width.toString());
    if (height) url.searchParams.append('height', height.toString());
  } else {
    url.searchParams.append('scale', scale.toString());
  }

  if (ultraMode) {
    url.searchParams.append('ultra_mode', 'true');
  }

  const response = await fetch(url.toString(), {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`Failed to start batch task: ${errorText}`);
  }

  return await response.json();
}

/**
 * Polls task status
 */
export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/status/${taskId}`);

  if (!response.ok) {
    throw new Error('Failed to get status');
  }

  return await response.json();
}

/**
 * Gets result blob
 */
export async function getTaskResult(taskId: string): Promise<Blob> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/result/${taskId}`);

  if (!response.ok) {
    throw new Error('Failed to get result');
  }

  const blob = await response.blob();
  return blob;
}
