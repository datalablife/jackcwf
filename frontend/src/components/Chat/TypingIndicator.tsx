/**
 * TypingIndicator Component
 *
 * Displays an animated typing indicator showing which users are currently typing.
 * Features:
 * - Animated dots with staggered bounce effect
 * - Shows typing user names
 * - Auto-dismiss after timeout
 *
 * Usage:
 * ```tsx
 * <TypingIndicator typingUsers={['Alice', 'Bob']} />
 * ```
 */

import React from 'react';

interface TypingIndicatorProps {
  typingUsers: string[];
}

/**
 * TypingIndicator - Animated typing indicator
 *
 * Shows animated dots with bounce animation to indicate that users are typing.
 * Displays user names who are currently typing.
 *
 * @param typingUsers - Array of user names currently typing
 */
export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ typingUsers }) => {
  if (typingUsers.length === 0) {
    return null;
  }

  const typingText = typingUsers.length === 1
    ? `${typingUsers[0]} is typing`
    : `${typingUsers.join(', ')} are typing`;

  return (
    <div className="max-w-4xl mx-auto flex items-center gap-3 py-4 text-slate-600">
      <div className="flex gap-1">
        <div
          className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
          style={{ animationDelay: '0s' }}
        />
        <div
          className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
          style={{ animationDelay: '0.2s' }}
        />
        <div
          className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
          style={{ animationDelay: '0.4s' }}
        />
      </div>
      <span className="text-sm">{typingText}</span>
    </div>
  );
};

export default TypingIndicator;
