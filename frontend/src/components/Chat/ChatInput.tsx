/**
 * ChatInput Component
 *
 * Message submission form with:
 * - React Hook Form + Zod validation
 * - Character count display
 * - Send on Enter/Cmd+Enter shortcuts
 * - Disabled state during submission
 * - Auto-expanding textarea
 *
 * Usage:
 * ```tsx
 * <ChatInput
 *   onSubmit={handleSendMessage}
 *   isLoading={false}
 *   maxLength={2000}
 * />
 * ```
 */

import React, { useRef, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

// Validation schema
const chatInputSchema = z.object({
  message: z
    .string()
    .min(1, 'Message cannot be empty')
    .max(2000, 'Message exceeds 2000 characters')
    .trim()
});

type ChatInputFormData = z.infer<typeof chatInputSchema>;

interface ChatInputProps {
  onSubmit: (message: string) => Promise<void>;
  isLoading?: boolean;
  placeholder?: string;
  maxLength?: number;
}

/**
 * ChatInput - Message submission form component
 *
 * Features:
 * - Real-time character count
 * - Auto-expanding textarea
 * - Send on Enter/Cmd+Enter
 * - Shift+Enter for line break
 * - Disabled during submission
 * - Loading state indication
 * - Validation error display
 *
 * @param onSubmit - Async function to handle message submission
 * @param isLoading - Whether form is submitting
 * @param placeholder - Custom textarea placeholder
 * @param maxLength - Max message length (default 2000)
 */
export const ChatInput: React.FC<ChatInputProps> = ({
  onSubmit,
  isLoading = false,
  placeholder = 'Type your message... (Cmd/Ctrl + Enter to send)',
  maxLength = 2000
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    watch
  } = useForm<ChatInputFormData>({
    resolver: zodResolver(chatInputSchema),
    mode: 'onChange'
  });

  const { ref: registerRef, ...registerProps } = register('message', {
    maxLength: maxLength
  });

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const messageValue = watch('message') || '';
  const charCount = messageValue.length;
  const isOverLimit = charCount > maxLength;
  const isDisabled = isSubmitting || isLoading || isOverLimit;

  // Auto-expand textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [messageValue]);

  // Handle form submission
  const handleFormSubmit = async (data: ChatInputFormData) => {
    try {
      await onSubmit(data.message.trim());
      reset();
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } catch (error) {
      console.error('Error submitting message:', error);
    }
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Cmd/Ctrl + Enter to send
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit(handleFormSubmit)();
    }

    // Shift + Enter for line break (default behavior)
    if (e.shiftKey && e.key === 'Enter') {
      return; // Allow default line break
    }

    // Regular Enter to send
    if (!e.shiftKey && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit(handleFormSubmit)();
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="w-full">
      <div className="relative bg-background/80 backdrop-blur-xl border border-border/50 rounded-2xl shadow-lg transition-all duration-200 focus-within:shadow-xl focus-within:border-primary/30 focus-within:ring-1 focus-within:ring-primary/20">
        {/* Textarea */}
        <textarea
          ref={(el) => {
            textareaRef.current = el;
            if (registerRef) registerRef(el);
          }}
          {...registerProps}
          placeholder={placeholder}
          disabled={isDisabled}
          onKeyDown={handleKeyDown}
          className={`w-full px-4 py-4 pr-14 bg-transparent border-none resize-none focus:outline-none focus:ring-0 transition-colors placeholder:text-muted-foreground/50 text-base leading-relaxed ${isDisabled ? 'cursor-not-allowed opacity-60' : ''
            }`}
          rows={1}
          style={{ maxHeight: '200px', minHeight: '60px' }}
        />

        {/* Bottom Actions */}
        <div className="absolute bottom-2 right-2 flex items-center gap-2">
          {/* Character Count (Only show when typing) */}
          {charCount > 0 && (
            <span className={`text-[10px] font-medium transition-colors mr-2 ${isOverLimit ? 'text-destructive' : 'text-muted-foreground/50'
              }`}>
              {charCount}/{maxLength}
            </span>
          )}

          {/* Send Button */}
          <button
            type="submit"
            disabled={isDisabled || !messageValue.trim()}
            className={`p-2 rounded-xl transition-all duration-200 flex items-center justify-center ${isDisabled || !messageValue.trim()
                ? 'bg-muted text-muted-foreground cursor-not-allowed opacity-50'
                : 'bg-primary text-primary-foreground hover:bg-primary/90 hover:shadow-md hover:-translate-y-0.5 active:translate-y-0'
              }`}
            title="Send message (Cmd/Ctrl + Enter)"
          >
            {isSubmitting || isLoading ? (
              <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Error Messages */}
      {errors.message && (
        <div className="mt-2 text-xs text-destructive flex items-center gap-1.5 px-2 animate-enter">
          <span>⚠️</span>
          {errors.message.message}
        </div>
      )}

      {/* Helper Text */}
      <div className="mt-2 px-2 flex justify-between items-center text-[10px] text-muted-foreground/50 select-none">
        <div className="flex gap-3">
          <span>Shift + Enter for new line</span>
        </div>
        <span>Cmd + Enter to send</span>
      </div>
    </form>
  );
};

export default ChatInput;
