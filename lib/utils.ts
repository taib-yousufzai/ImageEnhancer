export function formatFileSize(bytes: number): string {
  const megabytes = bytes / 1048576;
  return `${megabytes.toFixed(2)} MB`;
}
