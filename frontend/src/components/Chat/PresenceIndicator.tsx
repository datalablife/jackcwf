/**
 * PresenceIndicator Component
 *
 * Displays presence of users in a thread (online, typing, away, offline)
 * Features:
 * - User status indicators with color coding
 * - Typing status
 * - Animated online indicator
 * - User list with status
 *
 * Usage:
 * ```tsx
 * <PresenceIndicator users={presenceUsers} currentUserId="user1" />
 * ```
 */

import React from 'react';
import { PresenceUser } from '../../types';

interface PresenceIndicatorProps {
  users: PresenceUser[];
  currentUserId?: string;
  maxVisible?: number;
}

/**
 * PresenceIndicator - Shows online users and their status
 *
 * Displays user presence status with visual indicators
 *
 * @param users - Array of users with their presence status
 * @param currentUserId - Current user ID (to hide from list)
 * @param maxVisible - Maximum number of users to display (default: 5)
 */
export const PresenceIndicator: React.FC<PresenceIndicatorProps> = ({
  users,
  currentUserId,
  maxVisible = 5,
}) => {
  // Filter out current user and sort by status
  const otherUsers = users
    .filter((user) => user.userId !== currentUserId)
    .sort((a, b) => {
      const statusOrder = { typing: 0, online: 1, away: 2, offline: 3 };
      return statusOrder[a.status] - statusOrder[b.status];
    });

  if (otherUsers.length === 0) {
    return null;
  }

  const visibleUsers = otherUsers.slice(0, maxVisible);
  const hiddenCount = Math.max(0, otherUsers.length - maxVisible);

  const getStatusColor = (status: PresenceUser['status']) => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'typing':
        return 'bg-blue-500';
      case 'away':
        return 'bg-yellow-500';
      case 'offline':
        return 'bg-gray-400';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = (status: PresenceUser['status']) => {
    switch (status) {
      case 'online':
        return 'Online';
      case 'typing':
        return 'Typing';
      case 'away':
        return 'Away';
      case 'offline':
        return 'Offline';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-muted/30">
      <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
        Online
      </span>

      <div className="flex items-center gap-2 flex-wrap">
        {visibleUsers.map((user) => (
          <div
            key={user.userId}
            className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-card border border-border hover:border-primary/50 transition-colors"
            title={`${user.username} - ${getStatusText(user.status)}`}
          >
            {/* Status indicator */}
            <div className="relative w-2 h-2 flex-shrink-0">
              <div
                className={`w-2 h-2 rounded-full ${getStatusColor(user.status)} ${
                  user.status === 'online' ? 'animate-pulse' : ''
                }`}
              />
            </div>

            {/* Username */}
            <span className="text-xs text-foreground truncate max-w-[100px]">
              {user.username}
            </span>

            {/* Typing indicator */}
            {user.status === 'typing' && (
              <div className="flex gap-0.5">
                <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" />
                <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            )}
          </div>
        ))}

        {/* Show more indicator */}
        {hiddenCount > 0 && (
          <div className="text-xs text-muted-foreground px-2 py-1">
            +{hiddenCount} more
          </div>
        )}
      </div>

      {/* Total count */}
      <div className="ml-auto text-xs text-muted-foreground">
        {otherUsers.length} {otherUsers.length === 1 ? 'user' : 'users'} online
      </div>
    </div>
  );
};

export default PresenceIndicator;
