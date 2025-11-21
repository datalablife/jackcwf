/**
 * 消息导出服务
 *
 * 支持将对话消息导出为 JSON 或 PDF 格式
 * - JSON 导出：原始消息数据，易于处理
 * - PDF 导出：格式化文档，易于阅读和分享
 */

import { ChatMessage } from '../types';
import html2pdf from 'html2pdf.js';

/**
 * 导出选项接口
 */
interface ExportOptions {
  threadId: string;
  threadTitle?: string;
  includeMetadata?: boolean;
}

/**
 * JSON 导出 - 导出消息列表为 JSON 格式
 *
 * @param messages 消息列表
 * @param options 导出选项
 */
export const exportAsJSON = (messages: ChatMessage[], options: ExportOptions): void => {
  const { threadId, threadTitle, includeMetadata = true } = options;

  // 构建导出数据结构
  const exportData: any = {
    metadata: includeMetadata ? {
      threadId,
      threadTitle: threadTitle || 'Untitled Conversation',
      exportDate: new Date().toISOString(),
      messageCount: messages.length,
    } : undefined,
    messages: messages.map((msg) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp,
      isStreaming: msg.isStreaming || false,
    })),
  };

  // 如果不包含元数据，移除 undefined 字段
  if (!includeMetadata) {
    delete exportData.metadata;
  }

  // 转换为 JSON 字符串（格式化）
  const jsonString = JSON.stringify(exportData, null, 2);

  // 创建 Blob 并触发下载
  const blob = new Blob([jsonString], { type: 'application/json' });
  triggerDownload(blob, `conversation-${threadId}-${Date.now()}.json`);
};

/**
 * PDF 导出 - 导出消息列表为 PDF 格式
 *
 * @param messages 消息列表
 * @param options 导出选项
 */
export const exportAsPDF = async (
  messages: ChatMessage[],
  options: ExportOptions
): Promise<void> => {
  const { threadId, threadTitle = 'Untitled Conversation' } = options;

  // 构建 HTML 内容
  const htmlContent = buildPDFContent(messages, threadTitle);

  // 创建临时容器
  const element = document.createElement('div');
  element.innerHTML = htmlContent;
  element.style.display = 'none';
  document.body.appendChild(element);

  // PDF 配置选项
  const pdfOptions = {
    margin: 10,
    filename: `conversation-${threadId}-${Date.now()}.pdf`,
    image: { type: 'jpeg' as const, quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { orientation: 'portrait' as const, unit: 'mm', format: 'a4' },
  };

  try {
    // 生成 PDF
    await html2pdf().set(pdfOptions).from(element).save();
  } catch (error) {
    console.error('PDF 导出失败:', error);
    throw new Error('无法生成 PDF 文件');
  } finally {
    // 清理临时元素
    document.body.removeChild(element);
  }
};

/**
 * 构建 PDF 内容的 HTML
 *
 * @param messages 消息列表
 * @param title 对话标题
 * @returns HTML 字符串
 */
function buildPDFContent(messages: ChatMessage[], title: string): string {
  const now = new Date();
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  };
  const exportDate = now.toLocaleString('zh-CN', options);

  const messagesHTML = messages
    .map((msg) => {
      const role = msg.role === 'user' ? '用户' : 'AI';
      const roleClass = msg.role === 'user' ? 'user-message' : 'assistant-message';

      return `
        <div class="message ${roleClass}">
          <div class="message-header">
            <strong>${role}</strong>
            <span class="timestamp">${formatTimestamp(msg.timestamp)}</span>
          </div>
          <div class="message-content">${escapeHTML(msg.content)}</div>
        </div>
      `;
    })
    .join('');

  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
          }
          .header {
            border-bottom: 3px solid #3b82f6;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
          }
          .header h1 {
            margin: 0 0 0.5rem 0;
            color: #1f2937;
            font-size: 1.8rem;
          }
          .header .meta {
            color: #6b7280;
            font-size: 0.9rem;
          }
          .messages {
            display: flex;
            flex-direction: column;
            gap: 1rem;
          }
          .message {
            padding: 1rem;
            border-radius: 0.5rem;
            page-break-inside: avoid;
          }
          .message.user-message {
            background-color: #f3f4f6;
            border-left: 4px solid #3b82f6;
          }
          .message.assistant-message {
            background-color: #f0fdf4;
            border-left: 4px solid #10b981;
          }
          .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
            font-weight: bold;
          }
          .message-header strong {
            color: #1f2937;
          }
          .message-header .timestamp {
            color: #9ca3af;
            font-size: 0.85rem;
            font-weight: normal;
          }
          .message-content {
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #374151;
          }
          .footer {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #d1d5db;
            color: #9ca3af;
            font-size: 0.85rem;
            text-align: center;
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>${escapeHTML(title)}</h1>
          <div class="meta">
            <p>导出时间: ${exportDate}</p>
            <p>消息总数: ${messages.length}</p>
          </div>
        </div>
        <div class="messages">
          ${messagesHTML}
        </div>
        <div class="footer">
          <p>此文件由 LangChain AI 对话系统生成</p>
        </div>
      </body>
    </html>
  `;
}

/**
 * 触发文件下载
 *
 * @param blob 文件数据
 * @param filename 文件名
 */
function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * 格式化时间戳
 *
 * @param timestamp 时间戳字符串、数字或 Date 对象
 * @returns 格式化后的时间字符串
 */
function formatTimestamp(timestamp?: string | number | Date): string {
  if (!timestamp) return '未知时间';

  try {
    const date = new Date(timestamp);
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    };
    return date.toLocaleString('zh-CN', options);
  } catch {
    return '未知时间';
  }
}

/**
 * HTML 转义 - 防止 XSS
 *
 * @param text 要转义的文本
 * @returns 转义后的 HTML 安全文本
 */
function escapeHTML(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return text.replace(/[&<>"']/g, (char) => map[char] || char);
}
