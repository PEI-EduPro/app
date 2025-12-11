import { useRef, useState } from "react";
import { Upload } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

interface XmlUploadButtonProps {
  subjectId: number;
}

export default function XmlUploadButton({ subjectId }: XmlUploadButtonProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const queryClient = useQueryClient();

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".xml")) {
      alert("Por favor, selecione um arquivo XML.");
      return;
    }

    setIsUploading(true);
    try {
      const xmlContent = await file.text();
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/questions/${subjectId}/XML`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/xml',
        },
        body: xmlContent,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      
      queryClient.invalidateQueries({ queryKey: ['questions', subjectId] });
      alert("Questões importadas com sucesso!");
    } catch (error) {
      console.error("Error uploading XML:", error);
      alert("Erro ao importar questões. Verifique o formato do arquivo.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <>
      <button
        onClick={handleButtonClick}
        disabled={isUploading}
        className="flex items-center gap-2 bg-[#3263A8] text-white px-4 py-2 rounded-lg hover:bg-[#2a5390] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Upload />
        {isUploading ? "Importando..." : "Importar questões"}
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
