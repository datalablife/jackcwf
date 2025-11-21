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
    <form onSubmit={handleSubmit(handleFormSubmit)} className="border-t border-slate-200 bg-white p-4">
      <div className="max-w-4xl mx-auto">
        {/* Input Wrapper */}
        <div className="relative flex gap-2">
          {/* Textarea */}
          <div className="flex-1 relative">
            <textarea
              ref={(el) => {
                textareaRef.current = el;
                if (registerRef) registerRef(el);
              }}
              {...registerProps}
              placeholder={placeholder}
              disabled={isDisabled}
              onKeyDown={handleKeyDown}
              className={`w-full px-4 py-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
                errors.message ? 'border-red-500' : 'border-slate-200'
              } ${isDisabled ? 'bg-slate-50 cursor-not-allowed opacity-60' : 'bg-white'}`}
              rows={1}
              style={{ maxHeight: '200px', minHeight: '44px' }}
            />

            {/* Character Count */}
            <div
              className={`absolute bottom-3 right-3 text-xs font-medium ${
                isOverLimit ? 'text-red-600' : 'text-slate-500'
              }`}
            >
              {charCount} / {maxLength}
            </div>
          </div>

          {/* Send Button */}
          <button
            type="submit"
            disabled={isDisabled}
            className={`px-4 py-3 rounded-lg font-medium transition-all ${
              isDisabled
                ? 'bg-slate-200 text-slate-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95'
            }`}
            title="Send message (Cmd/Ctrl + Enter)"
          >
            {isSubmitting || isLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span className="hidden sm:inline">Sending</span>
              </div>
            ) : (
              <span className="text-lg">⬆️</span>
            )}
          </button>
        </div>

        {/* Error Messages */}
        {errors.message && (
          <div className="mt-2 text-sm text-red-600 flex items-center gap-2">
            <span>⚠️</span>
            {errors.message.message}
          </div>
        )}

        {/* Helper Text */}
        <div className="mt-2 text-xs text-slate-500 flex gap-4">
          <span>Shift + Enter for line break</span>
          <span>Cmd/Ctrl + Enter to send</span>
        </div>
      </div>
    </form>
  );
};

export default ChatInput;
