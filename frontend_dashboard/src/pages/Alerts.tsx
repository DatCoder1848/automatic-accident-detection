import { Table, Button, Tag } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';

export default function Alerts() {
  const queryClient = useQueryClient();
  const { data: alerts = [], isLoading } = useQuery({ queryKey: ['alerts'], queryFn: () => api.get('/alerts').then(r => r.data) });

  const markRead = useMutation({
    mutationFn: (id: string) => api.patch(`/alerts/${id}/read`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  });

  const columns = [
    { title: 'Message', dataIndex: 'message', key: 'message' },
    { title: 'Sent At', dataIndex: 'sentAt', key: 'sentAt', render: (v: string) => new Date(v).toLocaleString() },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={s === 'UNREAD' ? 'red' : 'green'}>{s}</Tag> },
    { title: 'Actions', key: 'actions', render: (_: any, record: any) => (
      record.status === 'UNREAD' ? <Button size="small" onClick={() => markRead.mutate(record.id)}>Mark Read</Button> : null
    )},
  ];

  return <Table dataSource={alerts} columns={columns} rowKey="id" loading={isLoading} />;
}
