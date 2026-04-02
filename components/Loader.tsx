export default function Loader() {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className="w-12 h-12 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin" />
      <p className="mt-4 text-gray-600">Processing your image…</p>
    </div>
  );
}
