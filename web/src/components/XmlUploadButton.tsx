import { useRef } from "react";
import { Upload } from "lucide-react";

export default function XmlUploadButton() {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".xml")) {
      alert("Por favor, selecione um arquivo XML.");
      return;
    }

    console.log("Selected XML file:", file);
  };

  return (
    <>
      <button
        onClick={handleButtonClick}
        className="flex items-center gap-2 bg-[#3263A8] text-white px-4 py-2 rounded-lg hover:bg-[#2a5390] transition-colors"
      >
        <Upload />
        Importar questões
      </button>

      <input
        type="file"
        ref={fileInputRef}
        accept=".xml"
        onChange={handleFileChange}
        className="hidden"
      />
    </>
  );
}
