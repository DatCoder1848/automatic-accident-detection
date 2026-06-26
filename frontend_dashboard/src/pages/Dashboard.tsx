import { Card, Col, Row, Table, Statistic } from 'antd';
import { WarningOutlined, VideoCameraOutlined, BellOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';

export default function Dashboard() {
  const { data: accidents = [] } = useQuery({ queryKey: ['accidents'], queryFn: () => api.get('/accidents').then(r => r.data) });
  const { data: cameras = [] } = useQuery({ queryKey: ['cameras'], queryFn: () => api.get('/cameras').then(r => r.data) });
  const { data: alerts = [] } = useQuery({ queryKey: ['alerts'], queryFn: () => api.get('/alerts').then(r => r.data) });

  const today = new Date().toDateString();
  const todayAccidents = accidents.filter((a: any) => new Date(a.detectedAt).toDateString() === today);
  const activeCameras = cameras.filter((c: any) => c.status === 'ACTIVE');
  const unreadAlerts = alerts.filter((a: any) => a.status === 'UNREAD');

  const columns = [
    { title: 'Time', dataIndex: 'detectedAt', key: 'detectedAt', render: (v: string) => new Date(v).toLocaleString() },
    { title: 'Camera', dataIndex: ['camera', 'name'], key: 'camera' },
    { title: 'Severity', dataIndex: 'severity', key: 'severity' },
    { title: 'Status', dataIndex: 'status', key: 'status' },
  ];

  return (
    <>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card><Statistic title="Accidents Today" value={todayAccidents.length} prefix={<WarningOutlined />} /></Card>
        </Col>
        <Col span={8}>
          <Card><Statistic title="Active Cameras" value={activeCameras.length} prefix={<VideoCameraOutlined />} /></Card>
        </Col>
        <Col span={8}>
          <Card><Statistic title="Unread Alerts" value={unreadAlerts.length} prefix={<BellOutlined />} /></Card>
        </Col>
      </Row>
      <h3>Recent Accidents</h3>
      <Table dataSource={accidents.slice(0, 10)} columns={columns} rowKey="id" pagination={false} size="small" />
    </>
  );
}
