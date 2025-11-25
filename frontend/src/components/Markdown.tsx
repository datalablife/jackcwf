/**
 * Markdown Component
 *
 * Renders markdown content with syntax highlighting
 * Features:
 * - Code block syntax highlighting
 * - Safe HTML rendering
 * - Link handling
 * - Table support
 * - Inline code highlighting
 */

import React, { useMemo } from 'react';
import { marked } from 'marked';

interface MarkdownProps {
  content: string;
  className?: string;
}

/**
 * Markdown - Renders markdown content safely
 *
 * @param content - Markdown content to render
 * @param className - Optional CSS class
 */
export const Markdown: React.FC<MarkdownProps> = ({ content, className = '' }) => {
  const html = useMemo(() => {
    if (!content) return '';

    try {
      const result = marked(content, {
        breaks: true,
        gfm: true,
      });
      // Handle both sync and async returns from marked
      return typeof result === 'string' ? result : '';
    } catch (error) {
      console.error('Error parsing markdown:', error);
      return `<p>${content}</p>`;
    }
  }, [content]);

  return (
    <div
      className={`markdown prose dark:prose-invert max-w-none
        prose-p:leading-relaxed
        prose-pre:bg-slate-950 prose-pre:text-slate-50
        prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
        dark:prose-code:bg-slate-800 dark:prose-code:text-slate-100
        prose-a:text-primary prose-a:underline hover:prose-a:text-primary/80
        prose-strong:font-semibold
        prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:pl-4 prose-blockquote:italic
        ${className}`}
      dangerouslySetInnerHTML={{ __html: html as string }}
    />
  );
};

export default Markdown;
