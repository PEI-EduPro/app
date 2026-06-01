import { Trash2, Plus } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";

export interface ParsedOption {
  text: string;
  fraction: number;
}

export interface ParsedQuestion {
  text: string;
  options: ParsedOption[];
}

export interface ParsedTopic {
  name: string;
  questions: ParsedQuestion[];
}

export function updateTopic(
  topics: ParsedTopic[],
  ti: number,
  name: string,
): ParsedTopic[] {
  return topics.map((t, i) => (i === ti ? { ...t, name } : t));
}

export function updateQuestion(
  topics: ParsedTopic[],
  ti: number,
  qi: number,
  text: string,
): ParsedTopic[] {
  return topics.map((t, i) =>
    i !== ti
      ? t
      : {
          ...t,
          questions: t.questions.map((q, j) => (j === qi ? { ...q, text } : q)),
        },
  );
}

export function updateOption(
  topics: ParsedTopic[],
  ti: number,
  qi: number,
  oi: number,
  text: string,
): ParsedTopic[] {
  return topics.map((t, i) =>
    i !== ti
      ? t
      : {
          ...t,
          questions: t.questions.map((q, j) =>
            j !== qi
              ? q
              : {
                  ...q,
                  options: q.options.map((o, k) =>
                    k === oi ? { ...o, text } : o,
                  ),
                },
          ),
        },
  );
}

export function toggleCorrect(
  topics: ParsedTopic[],
  ti: number,
  qi: number,
  oi: number,
): ParsedTopic[] {
  return topics.map((t, i) =>
    i !== ti
      ? t
      : {
          ...t,
          questions: t.questions.map((q, j) =>
            j !== qi
              ? q
              : {
                  ...q,
                  options: q.options.map((o, k) => ({
                    ...o,
                    fraction: k === oi ? (o.fraction > 0 ? 0 : 100) : 0,
                  })),
                },
          ),
        },
  );
}

export function deleteQuestion(
  topics: ParsedTopic[],
  ti: number,
  qi: number,
): ParsedTopic[] {
  return topics
    .map((t, i) =>
      i !== ti
        ? t
        : { ...t, questions: t.questions.filter((_, j) => j !== qi) },
    )
    .filter((t) => t.questions.length > 0);
}

export function addOption(
  topics: ParsedTopic[],
  ti: number,
  qi: number,
): ParsedTopic[] {
  return topics.map((t, i) =>
    i !== ti
      ? t
      : {
          ...t,
          questions: t.questions.map((q, j) =>
            j !== qi
              ? q
              : { ...q, options: [...q.options, { text: "", fraction: 0 }] },
          ),
        },
  );
}

export function deleteOption(
  topics: ParsedTopic[],
  ti: number,
  qi: number,
  oi: number,
): ParsedTopic[] {
  return topics.map((t, i) =>
    i !== ti
      ? t
      : {
          ...t,
          questions: t.questions.map((q, j) =>
            j !== qi
              ? q
              : { ...q, options: q.options.filter((_, k) => k !== oi) },
          ),
        },
  );
}

function validateTopics(topics: ParsedTopic[]): string[] {
  const errors: string[] = [];
  topics.forEach((topic, ti) => {
    if (!topic.name.trim())
      errors.push(`Tópico ${ti + 1}: nome não pode estar vazio`);
    topic.questions.forEach((q, qi) => {
      const label = `Tópico "${topic.name || ti + 1}", questão ${qi + 1}`;
      if (!q.text.trim()) errors.push(`${label}: texto não pode estar vazio`);
      if (q.options.length < 2)
        errors.push(`${label}: deve ter pelo menos 2 opções`);
      if (q.options.some((o) => !o.text.trim()))
        errors.push(`${label}: opções não podem estar vazias`);
      if (!q.options.some((o) => o.fraction > 0))
        errors.push(`${label}: deve ter uma resposta correta`);
    });
  });
  return errors;
}

interface XmlPreviewModalProps {
  topics: ParsedTopic[];
  onTopicsChange: (topics: ParsedTopic[]) => void;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function XmlPreviewModal({
  topics,
  onTopicsChange,
  onConfirm,
  onCancel,
}: XmlPreviewModalProps) {
  const totalQuestions = topics.reduce((s, t) => s + t.questions.length, 0);
  const errors = validateTopics(topics);
  const isValid = errors.length === 0 && totalQuestions > 0;

  return (
    <Dialog open onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="max-w-1/2! max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Pré-visualização da importação</DialogTitle>
          <p className="text-muted-foreground text-sm">
            {topics.length} tópico(s) · {totalQuestions} questão(ões) — edite
            antes de confirmar
          </p>
        </DialogHeader>

        <div className="overflow-y-auto flex-1 space-y-5 pr-1 discrete-scrollbar">
          {topics.map((topic, ti) => (
            <div key={ti}>
              <Input
                className={`font-semibold text-sm mb-2 h-7 ${!topic.name.trim() ? "border-destructive" : ""}`}
                value={topic.name}
                onChange={(e) =>
                  onTopicsChange(updateTopic(topics, ti, e.target.value))
                }
              />

              <ul className="space-y-3">
                {topic.questions.map((q, qi) => {
                  const noCorrect = !q.options.some((o) => o.fraction > 0);
                  const tooFewOptions = q.options.length < 2;
                  return (
                    <li
                      key={qi}
                      className={`border rounded-md p-3 text-sm space-y-2 ${noCorrect || tooFewOptions || !q.text.trim() ? "border-destructive" : ""}`}
                    >
                      <div className="flex gap-2 items-start">
                        <Input
                          className={`flex-1 h-7 text-sm font-medium ${!q.text.trim() ? "border-destructive" : ""}`}
                          value={q.text}
                          onChange={(e) =>
                            onTopicsChange(
                              updateQuestion(topics, ti, qi, e.target.value),
                            )
                          }
                        />
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 shrink-0 text-destructive hover:text-destructive cursor-pointer"
                          onClick={() =>
                            onTopicsChange(deleteQuestion(topics, ti, qi))
                          }
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>

                      <ul className="space-y-1 pl-2">
                        {q.options.map((opt, oi) => (
                          <li key={oi} className="flex gap-2 items-center">
                            <Button
                              title="Marcar como correta"
                              onClick={() =>
                                onTopicsChange(
                                  toggleCorrect(topics, ti, qi, oi),
                                )
                              }
                              className={`w-5 h-5 shrink-0 rounded border text-xs font-bold transition-colors bg-transparent cursor-pointer p-0 ${
                                opt.fraction > 0
                                  ? "bg-green-500 border-green-500 text-white"
                                  : "border-muted-foreground text-muted-foreground"
                              }`}
                            >
                              {String.fromCharCode(97 + oi)}
                            </Button>
                            <Input
                              className={`flex-1 h-6 text-xs ${!opt.text.trim() ? "border-destructive" : ""}`}
                              value={opt.text}
                              onChange={(e) =>
                                onTopicsChange(
                                  updateOption(
                                    topics,
                                    ti,
                                    qi,
                                    oi,
                                    e.target.value,
                                  ),
                                )
                              }
                            />
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-6 w-6 shrink-0 text-muted-foreground hover:text-destructive cursor-pointer"
                              onClick={() =>
                                onTopicsChange(deleteOption(topics, ti, qi, oi))
                              }
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </li>
                        ))}
                        <li>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 text-xs gap-1 px-2 cursor-pointer"
                            onClick={() =>
                              onTopicsChange(addOption(topics, ti, qi))
                            }
                          >
                            <Plus className="h-3 w-3" /> Opção
                          </Button>
                        </li>
                      </ul>

                      {(noCorrect || tooFewOptions) && (
                        <p className="text-destructive text-xs">
                          {tooFewOptions
                            ? "Mínimo de 2 opções."
                            : "Selecione uma resposta correta."}
                        </p>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        {!isValid && errors.length > 0 && (
          <ul className="text-destructive text-xs space-y-0.5 pt-1 border-t">
            {errors.map((e, i) => (
              <li key={i}>• {e}</li>
            ))}
          </ul>
        )}

        <DialogFooter className="flex-row justify-start!">
          <Button
            className="cursor-pointer"
            variant="outline"
            onClick={onCancel}
          >
            Cancelar
          </Button>
          <Button
            className="cursor-pointer"
            onClick={onConfirm}
            disabled={!isValid}
          >
            Confirmar importação
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
