import React from "react";

export const Skeleton: React.FC<{
  className?: string;
  width?: string;
  height?: string;
}> = ({ className = "", width, height }) => {
  return (
    <div
      aria-hidden="true"
      style={{ width, height }}
      className={`animate-pulse rounded-md bg-[#E2E5EA]/70 ${className}`}
    />
  );
};
