import LibraryBrowser from "../components/LibraryBrowser";

export default function LibraryPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Mi biblioteca</h1>
      <LibraryBrowser />
    </div>
  );
}
