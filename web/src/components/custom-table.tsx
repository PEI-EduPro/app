import {
  type Column,
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type OnChangeFn,
  type Row,
  type RowSelectionState,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowUpDown } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";

import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useState } from "react";

interface CustomTableProps {
  isSelectable?: boolean;
  data: Record<string, string>[];
  rowNumber?: number;
  rowSelection: Record<string, string>[];
  onChange: (selected: Record<string, string>[]) => void;
}

export function CustomTable(props: CustomTableProps) {
  const { isSelectable, data, rowNumber = 10, rowSelection, onChange } = props;
  const [sorting, setSorting] = useState<SortingState>([]);

  const keys = data[0] ? Object.keys(data[0]) : [];

  const selectColumn: ColumnDef<Record<string, string>> = {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && "indeterminate")
        }
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
        className="cursor-pointer"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
        className="cursor-pointer"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  };

  const dataColumns = keys.map((key) => ({
    accessorKey: key,
    header: ({ column }: { column: Column<Record<string, string>> }) => (
      <Button
        variant="ghost"
        className="capitalize cursor-pointer"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        {key}
        <ArrowUpDown />
      </Button>
    ),
    cell: ({ row }: { row: Row<Record<string, string>> }) => (
      <div>{row.getValue(key)}</div>
    ),
  })) as ColumnDef<Record<string, string>>[];

  const columns = isSelectable ? [selectColumn, ...dataColumns] : dataColumns;

  const handleRowSelectionChange: OnChangeFn<RowSelectionState> = (updater) => {
    const newSelection =
      typeof updater === "function"
        ? updater(
            rowSelection.reduce(
              (acc, el) => {
                acc[el.id] = true;
                return acc;
              },
              {} as Record<string, boolean>
            )
          )
        : updater;

    const selectedIds = Object.keys(newSelection).filter(
      (key) => newSelection[key]
    );
    const selectedRows = data.filter((row) => selectedIds.includes(row.id));

    onChange(selectedRows);
  };

  const table = useReactTable({
    data: isSelectable ? data : rowSelection,
    columns,
    getRowId: (row) => row.id,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onRowSelectionChange: handleRowSelectionChange,
    state: {
      sorting,
      rowSelection: rowSelection.reduce(
        (acc, el) => {
          acc[el.id] = true;
          return acc;
        },
        {} as Record<string, boolean>
      ),
    },
    initialState: {
      pagination: {
        pageSize: rowNumber,
      },
    },
  });

  return (
    <div className="w-full h-full">
      {isSelectable && (
        <div className="flex items-center py-4">
          <Input
            placeholder="Filter emails..."
            value={(table.getColumn("email")?.getFilterValue() as string) ?? ""}
            onChange={(event) =>
              table.getColumn("email")?.setFilterValue(event.target.value)
            }
          />
        </div>
      )}
      <div className="flex-1 overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getAllCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center space-x-2 py-4">
        <div className="flex flex-row justify-between w-full">
          <Button
            className="cursor-pointer"
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Anterior
          </Button>
          <Button
            className="cursor-pointer"
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Próximo
          </Button>
        </div>
      </div>
    </div>
  );
}
