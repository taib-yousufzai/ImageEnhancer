export function validateFile(file: File): string | null {
  if (!file.type.startsWith('image/')) {
    return 'Please select a valid image file';
  }
  
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    return 'File size must be less than 5MB';
  }
  
  return null;
}
