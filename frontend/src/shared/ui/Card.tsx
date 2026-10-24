import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = "",
  onClick,
  hoverable = false,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-lg border border-[#E2E5EA] transition-all ${
        hoverable ? "hover:border-[#CBD2DC] cursor-pointer" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}> = ({ title, description, action, className = "" }) => (
  <div className={`p-4 sm:p-5 border-b border-[#E2E5EA] flex items-start justify-between gap-4 ${className}`}>
    <div>
      {title && <h3 className="text-base font-semibold text-[#1F2A44] leading-snug">{title}</h3>}
      {description && <p className="text-xs text-[#5B6475] mt-1 leading-normal">{description}</p>}
    </div>
    {action && <div className="flex-shrink-0">{action}</div>}
  </div>
);

export const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = "",
}) => <div className={`p-4 sm:p-5 ${className}`}>{children}</div>;

export const CardFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = "",
}) => (
  <div className={`p-4 sm:p-5 border-t border-[#E2E5EA] bg-[#F7F7F4]/50 rounded-b-lg ${className}`}>
    {children}
  </div>
);
