import UploadCard from '@/components/UploadCard';

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-2xl">
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-center mb-6 sm:mb-8 text-gray-900">
          AI Image Enhancer
        </h1>
        <UploadCard />
      </div>
    </main>
  );
}
