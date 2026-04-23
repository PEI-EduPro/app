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
      toast.error("Por favor, selecione um arquivo XML.", {
        position: "top-right",
      });
      return;
    }

    setIsUploading(true);
    toast.loading("A importar questões...", {
      position: "top-right",
    });
    try {
      const xmlContent = await file.text();

      await apiClient.post(`/questions/${subjectId}/XML`, xmlContent, {
        headers: { "Content-Type": "application/xml" },
      });

      queryClient.invalidateQueries({ queryKey: ["questions", subjectId] });
      toast.dismiss();
      toast.success("Questões importadas com sucesso!", {
        position: "top-right",
      });
    } catch {
      toast.dismiss();
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
        size="sm"
        onClick={handleButtonClick}
        disabled={isUploading}
        className="gap-1 cursor-pointer h-auto"
      >
        <Upload className="h-4 w-4" />
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
