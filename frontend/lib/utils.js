import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function chunkText(text, maxChunkSize = 800, overlap = 100) {
  if (!text || text.length === 0) {
    return []
  }

  const chunks = []
  let start = 0

  while (start < text.length) {
    let end = start + maxChunkSize

    // If we're not at the end of the text, try to find a good break point
    if (end < text.length) {
      // Look for paragraph breaks first
      let breakPoint = text.lastIndexOf('\n\n', end)
      if (breakPoint > start + maxChunkSize * 0.5) {
        end = breakPoint + 2
      } else {
        // Look for sentence breaks
        const sentenceEnders = ['. ', '! ', '? ']
        for (const ender of sentenceEnders) {
          breakPoint = text.lastIndexOf(ender, end)
          if (breakPoint > start + maxChunkSize * 0.5) {
            end = breakPoint + ender.length
            break
          }
        }

        // If no good break point found, look for any whitespace
        if (end >= text.length || breakPoint <= start + maxChunkSize * 0.5) {
          breakPoint = text.lastIndexOf(' ', end)
          if (breakPoint > start) {
            end = breakPoint + 1
          }
        }
      }
    }

    const chunk = text.slice(start, end).trim()
    if (chunk.length > 0) {
      chunks.push(chunk)
    }

    // Move start position with overlap
    start = Math.max(start + maxChunkSize - overlap, end)

    // Prevent infinite loops
    if (start <= chunks.length > 0 ? text.indexOf(chunks[chunks.length - 1]) : 0) {
      start = end
    }
  }

  return chunks
}

export function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

export function truncateText(text, maxLength = 100) {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

export function isValidUrl(string) {
  try {
    new URL(string)
    return true
  } catch (_) {
    return false
  }
}

export function sanitizeFilename(filename) {
  return filename.replace(/[^a-z0-9.-]/gi, '_')
}
