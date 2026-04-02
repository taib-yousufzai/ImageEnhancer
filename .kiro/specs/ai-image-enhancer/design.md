# Design Document: AI Image Enhancer Frontend

## Overview

The AI Image Enhancer is a Next.js 14 web application that provides a streamlined interface for users to upload images, send them to a backend API for enhancement, and download the processed results. The application emphasizes simplicity, performance, and user experience through a clean SaaS-style interface.

The architecture follows Next.js App Router conventions with a clear separation between UI components, API integration logic, and application state management. All file handling is done in-memory using browser APIs to ensure optimal performance and resource management.

## Architecture

### Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **Component Pattern**: Functional components with React hooks
- **State Management**: React useState and useEffect hooks
- **API Communication**: Fetch API with FormData

### Application Structure

```
app/
  page.tsx              # Main application page (server component wrapper)
  layout.tsx            # Root layout with metadata
components/
  UploadCard.tsx        # Main upload and enhancement UI (client component)
  Loader.tsx            # Loading indicator component
lib/
  api.ts                # API integration layer
  types.ts              # TypeScript type definitions
```

### Component Hierarchy

```
Page (Server Component)
└── UploadCard (Client Component)
    ├── Upload Zone (drag & drop + click)
    ├── Image Preview
    ├── Enhance Button
    ├── Loader
    └── Download Button
```

## Components and Interfaces

### 1. Main Page Component (app/page.tsx)

**Purpose**: Server component that renders the main application layout.

**Implementation**:
```typescript
export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-2xl">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-900">
          AI Image Enhancer
        </h1>
        <UploadCard />
      </div>
    </main>
  );
}
```

### 2. UploadCard Component (components/UploadCard.tsx)

**Purpose**: Client component managing the entire image enhancement workflow.

**State Management**:
```typescript
const [selectedFile, setSelectedFile] = useState<File | null>(null);
const [previewUrl, setPreviewUrl] = useState<string | null>(null);
const [isProcessing, setIsProcessing] = useState<boolean>(false);
const [error, setError] = useState<string | null>(null);
const [enhancedImageUrl, setEnhancedImageUrl] = useState<string | null>(null);
const [isDragging, setIsDragging] = useState<boolean>(false);
```

**Key Functions**:

- `handleFileSelect(file: File): void` - Validates and processes selected file
- `handleDragOver(e: DragEvent): void` - Handles drag over events
- `handleDragLeave(e: DragEvent): void` - Handles drag leave events
- `handleDrop(e: DragEvent): void` - Handles file drop
- `handleFileInputChange(e: ChangeEvent<HTMLInputElement>): void` - Handles file input change
- `handleEnhance(): Promise<void>` - Initiates enhancement process
- `handleDownload(): void` - Triggers download of enhanced image

**File Validation Logic**:
```typescript
function validateFile(file: File): string | null {
  // Check file type
  if (!file.type.startsWith('image/')) {
    return 'Please select a valid image file';
  }
  
  // Check file size (5MB limit)
  const maxSize = 5 * 1024 * 1024; // 5MB in bytes
  if (file.size > maxSize) {
    return 'File size must be less than 5MB';
  }
  
  return null; // Valid
}
```

**Resource Cleanup**:
```typescript
useEffect(() => {
  // Cleanup function to revoke object URLs
  return () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    if (enhancedImageUrl) {
      URL.revokeObjectURL(enhancedImageUrl);
    }
  };
}, [previewUrl, enhancedImageUrl]);
```

### 3. Loader Component (components/Loader.tsx)

**Purpose**: Displays animated loading indicator during processing.

**Implementation**:
```typescript
export default function Loader() {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className="w-12 h-12 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin" />
      <p className="mt-4 text-gray-600">Processing your image…</p>
    </div>
  );
}
```

### 4. API Integration Layer (lib/api.ts)

**Purpose**: Handles communication with the backend API.

**Interface**:
```typescript
export async function enhanceImage(file: File): Promise<Blob> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('https://YOUR_RENDER_BACKEND_URL/enhance', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`Enhancement failed: ${errorText}`);
  }
  
  const blob = await response.blob();
  
  // Verify blob is an image
  if (!blob.type.startsWith('image/')) {
    throw new Error('Invalid response: expected image data');
  }
  
  return blob;
}
```

## Data Models

### File Metadata

```typescript
interface FileMetadata {
  name: string;
  size: number;
  type: string;
  sizeInMB: string; // Formatted string like "2.45 MB"
}
```

### Application State

```typescript
interface UploadCardState {
  selectedFile: File | null;
  previewUrl: string | null;
  isProcessing: boolean;
  error: string | null;
  enhancedImageUrl: string | null;
  isDragging: boolean;
}
```

### API Response

The backend API returns a raw image blob with content-type `image/webp`. No JSON parsing is required.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified the following redundancies:

1. **File acceptance (1.2 and 1.4)**: Both test that valid files result in state updates. These can be combined into one property about file selection.

2. **Error handling (3.6 and 3.7)**: Both test that API failures throw errors. These can be combined into one comprehensive error property.

3. **Resource cleanup (2.5 and 5.5)**: Both test URL revocation. These can be combined into one property about object URL lifecycle management.

4. **Loading state (4.6 and 6.3)**: Both test that isProcessing is cleared after completion. These represent the same behavior.

5. **Button state (3.1 and 3.2)**: Both test button disabled state under different conditions. These can be combined into one property about button enablement logic.

After reflection, the unique testable properties are:

- File validation (type and size)
- File selection and preview creation
- File size formatting
- Object URL lifecycle management
- Button enablement logic
- API request formatting
- API response handling (success and error)
- Loading state transitions
- Download functionality
- Error message display and clearing

### Properties

**Property 1: File type validation**
*For any* file with a MIME type not starting with "image/", the validation function should return an error message indicating invalid file type.
**Validates: Requirements 1.5, 1.6**

**Property 2: File size validation**
*For any* file with size greater than 5MB (5,242,880 bytes), the validation function should return an error message indicating the file is too large.
**Validates: Requirements 1.7**

**Property 3: Valid file acceptance**
*For any* file with an image MIME type and size ≤ 5MB, the validation function should return null (no error).
**Validates: Requirements 1.5**

**Property 4: File selection creates preview**
*For any* valid image file that is selected, the application should create a non-null object URL for preview display.
**Validates: Requirements 1.2, 1.4, 2.1**

**Property 5: File size formatting**
*For any* file size in bytes, the formatted size string should equal the size divided by 1,048,576 (bytes to MB), rounded to 2 decimal places, with " MB" suffix.
**Validates: Requirements 1.8, 2.4**

**Property 6: Object URL cleanup**
*For any* object URL that is created, when the component unmounts or a new file is selected, URL.revokeObjectURL should be called with that URL.
**Validates: Requirements 2.5, 5.5**

**Property 7: Button disabled when no file**
*For any* application state where selectedFile is null, the enhance button should be disabled.
**Validates: Requirements 3.1**

**Property 8: Button disabled during processing**
*For any* application state where isProcessing is true, the enhance button should be disabled.
**Validates: Requirements 3.2**

**Property 9: API request format**
*For any* valid file passed to enhanceImage, the function should create FormData with a "file" field containing that file.
**Validates: Requirements 3.4**

**Property 10: API success handling**
*For any* successful API response containing image data, the enhanceImage function should return a blob with an image MIME type.
**Validates: Requirements 3.5**

**Property 11: API error handling**
*For any* failed API response (non-ok status or network error), the enhanceImage function should throw an error.
**Validates: Requirements 3.6, 3.7**

**Property 12: Loading state activation**
*For any* enhance action, the isProcessing state should immediately become true.
**Validates: Requirements 4.1**

**Property 13: Button text during processing**
*For any* application state where isProcessing is true, the enhance button text should be "Enhancing…".
**Validates: Requirements 4.4**

**Property 14: Loading state deactivation**
*For any* API response (success or error), the isProcessing state should become false.
**Validates: Requirements 4.6**

**Property 15: Download button display**
*For any* successful enhancement that produces an enhancedImageUrl, the download button should be displayed.
**Validates: Requirements 5.1**

**Property 16: Download filename**
*For any* download action, the downloaded file should be named "enhanced.webp".
**Validates: Requirements 5.3**

**Property 17: Enhanced image URL creation**
*For any* blob returned from the API, an object URL should be created for download.
**Validates: Requirements 5.4**

**Property 18: Error message display**
*For any* API error or validation error, the error state should contain a non-empty descriptive message.
**Validates: Requirements 6.1, 6.2**

**Property 19: Error clears loading**
*For any* error that occurs during processing, the isProcessing state should become false and the button should be re-enabled if a file is still selected.
**Validates: Requirements 6.4**

**Property 20: Error clearing**
*For any* new action (file selection, enhancement start), the error state should be cleared (set to null).
**Validates: Requirements 6.6**

**Property 21: Drag state visual feedback**
*For any* drag-over event on the upload area, the isDragging state should become true, providing visual feedback.
**Validates: Requirements 1.1**

## Error Handling

### Validation Errors

**File Type Errors**:
- Message: "Please select a valid image file"
- Trigger: File MIME type does not start with "image/"
- Recovery: User selects a different file

**File Size Errors**:
- Message: "File size must be less than 5MB"
- Trigger: File size exceeds 5,242,880 bytes
- Recovery: User selects a smaller file

### API Errors

**Network Errors**:
- Message: "Enhancement failed: [error details]"
- Trigger: Network request fails or times out
- Recovery: User retries enhancement

**Server Errors**:
- Message: "Enhancement failed: [server response]"
- Trigger: Backend returns non-ok status
- Recovery: User retries or contacts support

**Invalid Response Errors**:
- Message: "Invalid response: expected image data"
- Trigger: Backend returns non-image content type
- Recovery: User retries or reports issue

### Error State Management

All errors are stored in the `error` state variable and displayed prominently in the UI. Errors are automatically cleared when:
- User selects a new file
- User initiates a new enhancement
- Component unmounts

The application maintains a usable state even after errors - users can retry enhancement or select a different file without refreshing the page.

## Testing Strategy

### Dual Testing Approach

This application requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Specific file validation scenarios (empty file, exact 5MB file)
- UI interaction flows (drag and drop, click upload)
- Component rendering with different state combinations
- Error message display
- Download trigger mechanism

**Property-Based Tests**: Verify universal properties across all inputs
- File validation logic with random file sizes and types
- File size formatting with random byte values
- State transitions with random valid/invalid files
- API error handling with various error responses
- Object URL lifecycle management

### Property-Based Testing Configuration

**Library**: fast-check (for TypeScript/JavaScript)

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with format: `Feature: ai-image-enhancer, Property {number}: {property_text}`
- Each correctness property implemented by a single property-based test

**Example Test Structure**:
```typescript
// Feature: ai-image-enhancer, Property 2: File size validation
test('files larger than 5MB should be rejected', () => {
  fc.assert(
    fc.property(
      fc.integer({ min: 5_242_881, max: 100_000_000 }), // File sizes > 5MB
      (fileSize) => {
        const mockFile = new File([''], 'test.jpg', { 
          type: 'image/jpeg' 
        });
        Object.defineProperty(mockFile, 'size', { value: fileSize });
        
        const error = validateFile(mockFile);
        expect(error).toBe('File size must be less than 5MB');
      }
    ),
    { numRuns: 100 }
  );
});
```

### Testing Focus Areas

1. **File Validation**: Property tests for all validation rules
2. **State Management**: Unit tests for state transitions
3. **API Integration**: Mock-based tests for API calls
4. **Resource Management**: Tests for URL creation and cleanup
5. **Error Handling**: Property tests for error scenarios
6. **UI Interactions**: Unit tests for user actions

### Test Organization

```
__tests__/
  lib/
    api.test.ts           # API integration tests
    validation.test.ts    # File validation property tests
  components/
    UploadCard.test.tsx   # Component unit tests
    Loader.test.tsx       # Loader component tests
  properties/
    file-handling.test.ts # Property tests for file operations
    state-management.test.ts # Property tests for state transitions
```

### Mocking Strategy

- Mock `fetch` for API tests
- Mock `URL.createObjectURL` and `URL.revokeObjectURL` for resource tests
- Mock file input events for upload tests
- Use React Testing Library for component tests
