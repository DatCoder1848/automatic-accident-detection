import { Table, Select, Tag, Space } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import api from '../api/client';

const severityColors: Record<string, string> = { LOW: 'blue', MEDIUM: 'orange', HIGH: 'red', CRITICAL: 'magenta' };

export default function Accidents() {
  const [severity, setSeverity] = useState<string>();
  const [status, setStatus] = useState<string>();

  const { data: accidents = [], isLoading } = useQuery({
    queryKey: ['accidents', severity, status],
    queryFn: () => {
      const params = new URLSearchParams();
      if (severity) params.set('severity', severity);
      if (status) params.set('status', status);
      return api.get(`/accidents?${params}`).then(r => r.data);
    },
  });

  const columns = [
    { title: 'Time', dataIndex: 'detectedAt', key: 'detectedAt', render: (v: string) => new Date(v).toLocaleString() },
    { title: 'Camera', dataIndex: ['camera', 'name'], key: 'camera' },
    { title: 'Confidence', dataIndex: 'confidence', key: 'confidence', render: (v: number) => `${(v * 100).toFixed(0)}%` },
    { title: 'Severity', dataIndex: 'severity', key: 'severity', render: (s: string) => <Tag color={severityColors[s]}>{s}</Tag> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag>{s}</Tag> },
  ];

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Select placeholder="Filter severity" allowClear onChange={setSeverity} style={{ width: 150 }}
          options={['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(v => ({ value: v, label: v }))} />
        <Select placeholder="Filter status" allowClear onChange={setStatus} style={{ width: 150 }}
          options={['PENDING', 'CONFIRMED', 'FALSE_ALARM', 'RESOLVED'].map(v => ({ value: v, label: v }))} />
      </Space>
      <Table dataSource={accidents} columns={columns} rowKey="id" loading={isLoading} />
    </>
  );
}
