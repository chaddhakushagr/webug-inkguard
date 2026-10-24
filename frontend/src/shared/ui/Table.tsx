import React from "react";

export const Table: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = "",
}) => (
  <div className={`overflow-x-auto rounded-lg border border-[#E2E5EA] bg-white ${className}`}>
    <table className="min-w-full divide-y divide-[#E2E5EA] text-left text-sm text-[#1F2A44]">
      {children}
    </table>
  </div>
);

export const TableHead: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = "",
}) => <thead className={`bg-[#F7F7F4] text-xs font-semibold text-[#5B6475] uppercase tracking-wider ${className}`}>{children}</thead>;

export const TableBody: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = "",
}) => <tbody className={`divide-y divide-[#E2E5EA] bg-white ${className}`}>{children}</tbody>;

export const TableRow: React.FC<{
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}> = ({ children, className = "", onClick, hoverable = true }) => (
  <tr
    onClick={onClick}
    className={`${hoverable ? "hover:bg-[#F7F7F4]/60 transition-colors" : ""} ${
      onClick ? "cursor-pointer" : ""
    } ${className}`}
  >
    {children}
  </tr>
);

export const TableHeaderCell: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = "",
}) => <th className={`px-4 py-3 font-semibold ${className}`}>{children}</th>;

export const TableCell: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = "",
}) => <td className={`px-4 py-3 whitespace-nowrap text-sm ${className}`}>{children}</td>;
