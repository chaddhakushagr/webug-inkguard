import React from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  breadcrumbs,
  actions,
  className = "",
}) => {
  return (
    <div className={`mb-6 sm:mb-8 ${className}`}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav aria-label="Breadcrumb" className="mb-2">
          <ol className="flex items-center space-x-1.5 text-xs text-[#5B6475]">
            {breadcrumbs.map((item, idx) => (
              <li key={idx} className="flex items-center">
                {idx > 0 && <ChevronRight className="w-3.5 h-3.5 mx-1 text-[#CBD2DC]" />}
                {item.href ? (
                  <Link href={item.href} className="hover:text-[#0F766E] transition-colors">
                    {item.label}
                  </Link>
                ) : (
                  <span className="font-medium text-[#1F2A44]">{item.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1F2A44] tracking-tight">{title}</h1>
          {description && <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">{description}</p>}
        </div>
        {actions && <div className="flex items-center gap-2.5 flex-wrap">{actions}</div>}
      </div>
    </div>
  );
};
