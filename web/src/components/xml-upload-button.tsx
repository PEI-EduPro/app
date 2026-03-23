import { useRef, useState } from "react";
import { Upload } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "./ui/button";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";

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

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".xml")) {
      alert("Por favor, selecione um arquivo XML.");
      return;
    }

    setIsUploading(true);
    try {
      const xmlContent = await file.text();

      await apiClient.post(`/questions/${subjectId}/XML`, xmlContent, {
        headers: { "Content-Type": "application/xml" },
      });

      queryClient.invalidateQueries({ queryKey: ["questions", subjectId] });
      toast.success("Questões importadas com sucesso!", {
        position: "top-right",
      });
    } catch {
      toast.error("Ocorreu um erro, tente novamente mais tarde.", {
        position: "top-right",
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <>
      <Button
        onClick={handleButtonClick}
        disabled={isUploading}
        className="flex items-center gap-2 bg-[#3263A8] text-white px-4 py-2 rounded-lg hover:bg-[#2a5390] transition-colors disabled:opacity-50 disabled:cursor-not-allowed h-[40px] cursor-pointer"
      >
        <Upload className="h-5! w-5!" />
        {isUploading ? "Importando..." : "Importar questões"}
      </Button>

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
