import { useState, useEffect } from "react";
import { X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";

interface TopicModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string) => void;
  onUpdate: (id: number, name: string) => void;
  editingTopic: { id: number; name: string } | null;
}

export default function TopicModal({
  isOpen,
  onClose,
  onCreate,
  onUpdate,
  editingTopic,
}: TopicModalProps) {
  const [topicName, setTopicName] = useState("");

  useEffect(() => {
    if (editingTopic) {
      setTopicName(editingTopic.name);
    } else {
      setTopicName("");
    }
  }, [editingTopic]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topicName.trim()) {
      if (editingTopic) {
        onUpdate(editingTopic.id, topicName.trim());
      } else {
        onCreate(topicName.trim());
      }
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <Card className="w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">
              {editingTopic ? "Editar Tópico" : "Novo Tópico"}
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
            <div className="mb-6">
              <Label htmlFor="topicName" className="mb-2">
                Nome do Tópico
              </Label>
              <Input
                value={topicName}
                onChange={(e) => setTopicName(e.target.value)}
                placeholder="Ex: Instruções de decisão, Recursividade, etc."
                autoFocus
              />
            </div>

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
                className="cursor-pointer"
                disabled={!topicName.trim()}
              >
                {editingTopic ? "Guardar" : "Criar"}
              </Button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
}
