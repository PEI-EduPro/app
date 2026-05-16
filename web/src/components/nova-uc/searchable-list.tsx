import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";

function formatName(p: {
  firstName?: string;
  lastName?: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  email?: string;
}) {
  return p.firstName && p.lastName
    ? `${p.firstName} ${p.lastName}`
    : p.first_name && p.last_name
      ? `${p.first_name} ${p.last_name}`
      : p.username || p.email || "";
}

type Item = {
  id: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  first_name?: string;
  last_name?: string;
  username?: string;
};

export function SearchableList({
  items,
  allItems,
  search,
  onSearch,
  selected,
  onToggle,
  loading = false,
}: {
  items: Item[];
  allItems?: Item[];
  search: string;
  onSearch: (v: string) => void;
  selected: string | string[];
  onToggle: (id: string) => void;
  multi?: boolean;
  loading?: boolean;
}) {
  const selectedIds = Array.isArray(selected)
    ? selected
    : selected
      ? [selected]
      : [];

  const sourceForSelected = allItems ?? items;
  const selectedItems = (id: string) =>
    sourceForSelected.filter((p) => p.id === id).map(formatName);

  return (
    <div className="flex flex-col gap-2">
      {selectedIds.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selectedIds.map((p) => (
            <span
              key={p}
              onClick={() => onToggle(p)}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary cursor-pointer hover:bg-red-100 hover:text-red-600 transition-colors"
            >
              {selectedItems(p)} ×
            </span>
          ))}
        </div>
      )}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Pesquisar por nome ou email..."
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          className="pl-9 shadow-none"
        />
      </div>
      <div className="border rounded-md overflow-y-auto h-48">
        {loading ? (
          <div className="p-3 text-sm text-muted-foreground">A carregar...</div>
        ) : (
          items.filter((p) => !selectedIds.includes(p.id)).length === 0 ? (
            <div className="p-3 text-sm text-muted-foreground">Nenhum resultado.</div>
          ) : (
            items
              .filter((p) => !selectedIds.includes(p.id))
              .map((p) => (
                <div
                  key={p.id}
                  onClick={() => onToggle(p.id)}
                  className="px-3 py-2 cursor-pointer text-sm hover:bg-muted/50 transition-colors"
                >
                  <div>{formatName(p)}</div>
                  {p.email && (
                    <div className="text-xs text-muted-foreground">{p.email}</div>
                  )}
                </div>
              ))
          )
        )}
      </div>
    </div>
  );
}
