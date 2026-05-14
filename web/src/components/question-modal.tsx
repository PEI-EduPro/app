import { useState, useEffect } from "react";
import { X, Plus, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { toast } from "sonner";

interface Question {
  id: number;
  text: string;
  options: Record<number, string>;
  answer: number;
}

interface QuestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (question: Omit<Question, "id">) => void;
  onUpdate: (questionId: number, question: Omit<Question, "id">) => void;
  editingQuestion: { topicId: number; question: Question } | null;
  topicId: number | null;
}

export default function QuestionModal({
  isOpen,
  onClose,
  onCreate,
  onUpdate,
  editingQuestion,
  topicId,
}: QuestionModalProps) {
  const [questionText, setQuestionText] = useState("");
  const [options, setOptions] = useState<{ id: number; value: string }[]>([
    { id: 1, value: "" },
    { id: 2, value: "" },
    { id: 3, value: "" },
    { id: 4, value: "" },
  ]);
  const [correctAnswer, setCorrectAnswer] = useState<number | null>(null);

  useEffect(() => {
    if (editingQuestion?.question) {
      const q = editingQuestion.question;
      setQuestionText(q.text);
      setOptions(
        Object.entries(q.options).map(([key, value]) => ({
          id: parseInt(key),
          value,
        })),
      );
      setCorrectAnswer(q.answer);
    } else if (isOpen) {
      setQuestionText("");
      setOptions([
        { id: 1, value: "" },
        { id: 2, value: "" },
        { id: 3, value: "" },
        { id: 4, value: "" },
      ]);
      setCorrectAnswer(null);
    }
  }, [editingQuestion, isOpen]);

  const optionValues = options.map((o) => o.value.trim().toLowerCase());
  const hasDuplicates = optionValues.length !== new Set(optionValues).size;
  const hasEmptyOptions = options.some((o) => !o.value.trim());
  const isValid =
    questionText.trim() !== "" &&
    !hasEmptyOptions &&
    correctAnswer !== null &&
    !hasDuplicates;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;

    const optionsObject: Record<number, string> = {};
    options.forEach((opt) => {
      optionsObject[opt.id] = opt.value.trim();
    });

    const questionData: Omit<Question, "id"> = {
      text: questionText.trim(),
      options: optionsObject,
      answer: correctAnswer!,
    };

    if (editingQuestion) {
      onUpdate(editingQuestion.question.id, questionData);
    } else if (topicId) {
      onCreate(questionData);
    }

    onClose();
  };

  const handleOptionChange = (id: number, value: string) => {
    setOptions(options.map((opt) => (opt.id === id ? { ...opt, value } : opt)));
  };

  const addOption = () => {
    const newId = Math.max(...options.map((opt) => opt.id)) + 1;
    setOptions([...options, { id: newId, value: "" }]);
  };

  const removeOption = (id: number) => {
    if (options.length <= 2) {
      toast.error("A questão deve ter pelo menos 2 opções", {
        position: "top-right",
      });
      return;
    }
    setOptions(options.filter((opt) => opt.id !== id));
    if (correctAnswer === id) setCorrectAnswer(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="px-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">
              {editingQuestion ? "Editar Questão" : "Nova Questão"}
            </h2>
            <Button
              variant="ghost"
              onClick={onClose}
              className="cursor-pointer"
            >
              <X className="h-6.25! w-6.25!" />
            </Button>
          </div>

          <form onSubmit={handleSubmit}>
            {/* Question Text */}
            <div className="mb-6">
              <Label className="block text-sm font-medium text-gray-700 mb-2">
                Texto da Questão<span className="text-red-500 ml-1">*</span>
              </Label>
              <Textarea
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition resize-none ${
                  questionText.trim() === ""
                    ? "border-red-300"
                    : "border-gray-300"
                }`}
                placeholder="Escreva a questão aqui..."
                rows={3}
              />
            </div>

            {/* Options */}
            <div className="flex flex-col mb-6 gap-2">
              <div className="flex items-center justify-between">
                <Label className="block text-sm font-medium text-gray-700">
                  Opções de Resposta
                </Label>
                <Button
                  variant="ghost"
                  onClick={addOption}
                  className="flex items-center gap-2 text-sm text-[#3263A8] hover:text-[#2a5390] cursor-pointer"
                >
                  <Plus size={16} />
                  Adicionar Opção
                </Button>
              </div>

              {(correctAnswer === null || hasDuplicates) && (
                <p className="text-sm text-red-500 mt-1">
                  {correctAnswer === null && hasDuplicates
                    ? "Selecione a resposta correta e remova as opções duplicadas."
                    : correctAnswer === null
                      ? "Selecione a resposta correta."
                      : "Não é permitido ter opções duplicadas."}
                </p>
              )}

              <div className="space-y-3">
                {options.map((option, index) => {
                  const isDuplicate =
                    option.value.trim() !== "" &&
                    optionValues.filter(
                      (v) => v === option.value.trim().toLowerCase(),
                    ).length > 1;
                  const isEmpty = option.value.trim() === "";

                  return (
                    <div
                      key={option.id}
                      className="flex items-center gap-3 group"
                    >
                      <Input
                        type="radio"
                        id={`option-${option.id}`}
                        name="correct-answer"
                        checked={correctAnswer === option.id}
                        onChange={() => setCorrectAnswer(option.id)}
                        className="h-5 w-5 text-blue-600"
                      />
                      <Label
                        htmlFor={`option-${option.id}`}
                        className="flex-1 flex items-center gap-3"
                      >
                        <span className="w-8 text-sm font-medium text-gray-500">
                          {index + 1}.
                        </span>
                        <Input
                          value={option.value}
                          onChange={(e) =>
                            handleOptionChange(option.id, e.target.value)
                          }
                          className={`flex-1 px-3 py-2 border rounded-lg outline-none transition placeholder:text-gray-300 ${
                            isDuplicate || isEmpty
                              ? "border-red-400 focus:ring-2 focus:ring-red-400"
                              : correctAnswer === option.id
                                ? "border-green-500 focus:ring-2 focus:ring-green-500 focus:border-green-500"
                                : "border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          }`}
                          placeholder={`Opção ${index + 1}`}
                        />
                      </Label>
                      {options.length > 2 && (
                        <Button
                          variant="ghost"
                          onClick={() => removeOption(option.id)}
                          className="p-2 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                          title="Remover opção"
                        >
                          <Trash2 size={16} />
                        </Button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <Button
                variant="destructive"
                onClick={onClose}
                className="cursor-pointer"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={!isValid}
                className="cursor-pointer"
              >
                {editingQuestion ? "Guardar" : "Criar"}
              </Button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
}
