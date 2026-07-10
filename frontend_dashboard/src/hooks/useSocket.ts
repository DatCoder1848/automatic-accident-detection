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

    socket.on('new-accident', (accident: any) => {
      notification.warning({
        message: '🚨 New Accident Detected',
        description: `Severity: ${accident.severity} | Confidence: ${(accident.confidence * 100).toFixed(0)}%`,
        placement: 'topRight',
        duration: 8,
      });
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['accidents'] });
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
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
