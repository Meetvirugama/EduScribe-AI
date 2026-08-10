import { useState, useEffect } from 'react';
import { API_BASE } from '../lib/api';

export function useProgressStream(videoId, token) {
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Reset state when video changes or processing completes/fails
    setProgress(null);
    setError(null);

    if (!videoId || !token) return;

    // Use SSE for real-time progress updates
    const url = `${API_BASE}/videos/${videoId}/progress/stream?token=${token}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.error) {
          setError(data.error);
          eventSource.close();
        } else {
          setProgress(data);
          if (data.status === 'COMPLETED' || data.status === 'FAILED') {
            eventSource.close();
          }
        }
      } catch (err) {
        console.error('Failed to parse SSE data', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE Error:', err);
      setError('Connection to progress stream lost.');
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [videoId, token]);

  return { progress, error };
}
