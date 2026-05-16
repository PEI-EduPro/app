import { useRef, useState } from "react";
import { Upload } from "lucide-react";
import { Button } from "../ui/button";
import { toast } from "sonner";
import { useImportQuestionsXml } from "@/hooks/use-questions";
import XmlPreviewModal, { type ParsedTopic } from "./xml-preview-modal";

interface XmlUploadButtonProps {
  subjectId: number;
  onPreviewOpenChange?: (open: boolean) => void;
}

function parseMoodleXml(xmlContent: string): ParsedTopic[] {
  const parser = new DOMParser();
  const doc = parser.parseFromString(xmlContent, "application/xml");
  const topics: Record<string, ParsedTopic> = {};

  for (const q of Array.from(doc.querySelectorAll("question"))) {
    const type = q.getAttribute("type");
    if (type !== "multichoice" && type !== "shortanswer") continue;

    const topicName =
      q.querySelector("name > text")?.textContent?.trim() ?? "Default Topic";

    if (!topics[topicName])
      topics[topicName] = { name: topicName, questions: [] };

    const rawText = q.querySelector("questiontext text")?.textContent ?? "";
    const questionText =
      new DOMParser()
        .parseFromString(rawText, "text/html")
        .body.textContent?.trim() ?? rawText;

    const options = Array.from(q.querySelectorAll("answer")).map((ans) => {
      const rawAns = ans.querySelector("text")?.textContent ?? "";
      const text =
        new DOMParser()
          .parseFromString(rawAns, "text/html")
          .body.textContent?.trim() ?? rawAns;
      return {
        text,
        fraction: parseFloat(ans.getAttribute("fraction") ?? "0"),
      };
    });

    topics[topicName].questions.push({ text: questionText, options });
  }

  return Object.values(topics);
}

function topicsToXml(topics: ParsedTopic[]): string {
  const questions = topics.flatMap((topic) =>
    topic.questions.map((q) => {
      const answers = q.options
        .map(
          (opt) =>
            `<answer fraction="${opt.fraction}"><text><![CDATA[${opt.text}]]></text></answer>`,
        )
        .join("");
      return `<question type="multichoice"><name><text>${topic.name}</text></name><questiontext><text><![CDATA[${q.text}]]></text></questiontext>${answers}</question>`;
    }),
  );
  return `<?xml version="1.0" encoding="UTF-8"?><quiz>${questions.join("")}</quiz>`;
}

export default function XmlUploadButton({ subjectId, onPreviewOpenChange }: XmlUploadButtonProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [topics, setTopics] = useState<ParsedTopic[] | null>(null);
  const { mutate, isPending } = useImportQuestionsXml(subjectId);

  const updateTopics = (value: ParsedTopic[] | null) => {
    setTopics(value);
    onPreviewOpenChange?.(value !== null);
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

    const parsed = parseMoodleXml(await file.text());
    if (parsed.length === 0) {
      toast.error("Nenhuma questão encontrada no ficheiro XML.", {
        position: "top-right",
      });
    } else {
      updateTopics(parsed);
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleConfirm = () => {
    if (!topics) return;
    mutate(topicsToXml(topics));
    updateTopics(null);
  };

  return (
    <>
      <Button
        size="sm"
        onClick={() => fileInputRef.current?.click()}
        disabled={isPending}
        className="gap-1 cursor-pointer"
      >
        <Upload className="h-4 w-4" />
        {isPending ? "Importando..." : "Importar questões"}
      </Button>

      <input
        type="file"
        ref={fileInputRef}
        accept=".xml"
        onChange={handleFileChange}
        className="hidden"
      />

      {topics && (
        <XmlPreviewModal
          topics={topics}
          onTopicsChange={updateTopics}
          onConfirm={handleConfirm}
          onCancel={() => updateTopics(null)}
        />
      )}
    </>
  );
}
