import { useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useQueryClient } from '@tanstack/react-query';
import { notification } from 'antd';

const SOCKET_URL = 'http://localhost:3000';

export function useSocket() {
  const socketRef = useRef<Socket | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    const socket = io(SOCKET_URL);
    socketRef.current = socket;

    // Thread 1: Instant alert - accident detected (no video yet)
    socket.on('new-accident', (accident: any) => {
      notification.warning({
        message: '🚨 New Accident Detected',
        description: `Severity: ${accident.severity} | Confidence: ${(accident.confidence * 100).toFixed(0)}%`,
        placement: 'topRight',
        duration: 8,
      });
      queryClient.invalidateQueries({ queryKey: ['accidents'] });
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    });

    // Thread 2: Video ready - evidence uploaded
    socket.on('accident-video-ready', (data: { accidentId: string; videoClipUrl: string }) => {
      notification.success({
        message: '📹 Video Evidence Ready',
        description: `Evidence video has been uploaded for accident.`,
        placement: 'topRight',
        duration: 5,
      });
      // Refresh the specific accident detail if currently viewing
      queryClient.invalidateQueries({ queryKey: ['accident', data.accidentId] });
      queryClient.invalidateQueries({ queryKey: ['accidents'] });
    });

    socket.on('accident-updated', () => {
      queryClient.invalidateQueries({ queryKey: ['accidents'] });
    });

    return () => {
      socket.disconnect();
    };
  }, [queryClient]);

  const getSocket = useCallback(() => socketRef.current, []);
  return { getSocket };
}
