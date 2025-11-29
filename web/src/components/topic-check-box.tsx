"use client"

import * as React from "react"
import {
  type ColumnDef,
  type ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const data: Subject[] = [
  { id: "1", name: "Arquiteturas" },
  { id: "2", name: "Definição de requisitos avançada" },
  { id: "3", name: "Introdução à tomada de decisão" },
]

export type Subject = {
  id: string
  name: string
}

export type TopicSelection = {
  id: string;
  name: string;
};

// Table columns
export const columns: ColumnDef<Subject>[] = [
  {
    id: "select",
    header: ({ table }) => {
      const allSelected = table.getIsAllPageRowsSelected()
      //const someSelected = table.getIsSomePageRowsSelected()

      return (
        <Checkbox
          checked={allSelected}                        // only true if all rows are selected
          //indeterminate={someSelected && !allSelected} // dash if some (but not all) are selected
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
        />
      )
    },
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "name",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="p-0 hover:bg-transparent"
      >
        Nome <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
  },
]

interface SubjectTableProps {
  selectedTopics: TopicSelection[]
  onChange: (topics: TopicSelection[]) => void
}

export function SubjectTable({ selectedTopics, onChange }: SubjectTableProps) {
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])

  // Initialize rowSelection from selectedTopics
  const [rowSelection, setRowSelection] = React.useState(
    selectedTopics.reduce((acc, topic) => ({ ...acc, [topic.id]: true }), {})
  )

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
      rowSelection,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  // Sync rowSelection changes back to RHF - MOVED AFTER table declaration
  React.useEffect(() => {
    const selectedRows = table.getFilteredSelectedRowModel().rows;
    const selectedTopics = selectedRows.map(row => ({
      id: row.original.id,
      name: row.original.name
    }));
    
    onChange(selectedTopics);
  }, [rowSelection, onChange, table])

  return (
    <div className="w-full space-y-4">
      {/* Search Input */}
      <div className="relative">
        <Input
          placeholder="Pesquisa por nome..."
          value={(table.getColumn("name")?.getFilterValue() as string) ?? ""}
          onChange={(e) =>
            table.getColumn("name")?.setFilterValue(e.target.value)
          }
        />
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} data-state={row.getIsSelected() && "selected"}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  Nenhum resultado encontrado.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Selection Info */}
      <div className="text-sm text-muted-foreground">
        {table.getFilteredSelectedRowModel().rows.length} de{" "}
        {table.getFilteredRowModel().rows.length} tópico(s) selecionado(s)
      </div>
    </div>
  )
}