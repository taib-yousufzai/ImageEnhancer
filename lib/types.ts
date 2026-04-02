export interface FileMetadata {
  name: string;
  size: number;
  type: string;
  sizeInMB: string;
}

export interface UploadCardState {
  selectedFile: File | null;
  previewUrl: string | null;
  isProcessing: boolean;
  error: string | null;
  enhancedImageUrl: string | null;
  isDragging: boolean;
}
