import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Descriptions, Tag, Button, Space, Select, Spin } from 'antd';
import { ArrowLeftOutlined, LoadingOutlined } from '@ant-design/icons';
import api from '../api/client';

const severityColors: Record<string, string> = { LOW: 'blue', MEDIUM: 'orange', HIGH: 'red', CRITICAL: 'magenta' };

export default function AccidentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: accident, isLoading } = useQuery({
    queryKey: ['accident', id],
    queryFn: () => api.get(`/accidents/${id}`).then(r => r.data),
    refetchInterval: (query) => {
      // Auto-refetch every 3s while waiting for video
      const data = query.state.data;
      return data && !data.videoClipUrl ? 3000 : false;
    },
  });

  const updateStatus = useMutation({
    mutationFn: (status: string) => api.patch(`/accidents/${id}`, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['accident', id] }),
  });

  if (isLoading) return <p>Loading...</p>;
  if (!accident) return <p>Accident not found</p>;

  return (
    <>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/accidents')} style={{ marginBottom: 16 }}>
        Back
      </Button>

      <Card title={`Accident — ${new Date(accident.detectedAt).toLocaleString()}`}>
        <Descriptions bordered column={2}>
          <Descriptions.Item label="Camera">{accident.camera?.name || 'Unknown'}</Descriptions.Item>
          <Descriptions.Item label="Location">{accident.camera?.location || '-'}</Descriptions.Item>
          <Descriptions.Item label="Confidence">{(accident.confidence * 100).toFixed(0)}%</Descriptions.Item>
          <Descriptions.Item label="Severity">
            <Tag color={severityColors[accident.severity]}>{accident.severity}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Space>
              <Tag>{accident.status}</Tag>
              <Select
                size="small"
                placeholder="Update"
                onChange={(v) => updateStatus.mutate(v)}
                options={['CONFIRMED', 'FALSE_ALARM', 'RESOLVED'].map(v => ({ value: v, label: v }))}
                style={{ width: 140 }}
              />
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Detected At">{new Date(accident.detectedAt).toLocaleString()}</Descriptions.Item>
          {accident.description && (
            <Descriptions.Item label="Description" span={2}>{accident.description}</Descriptions.Item>
          )}
          {accident.vehiclesInvolved?.length > 0 && (
            <Descriptions.Item label="Vehicles Involved" span={2}>{accident.vehiclesInvolved.join(', ')}</Descriptions.Item>
          )}
          {accident.latitude && (
            <Descriptions.Item label="GPS">{accident.latitude}, {accident.longitude}</Descriptions.Item>
          )}
        </Descriptions>

        {/* Thumbnail */}
        {accident.thumbnailUrl && (
          <div style={{ marginTop: 24 }}>
            <h4>Snapshot</h4>
            <img src={accident.thumbnailUrl} alt="Accident snapshot" style={{ maxWidth: 720, borderRadius: 8, width: '100%' }} />
          </div>
        )}

        {/* Video Section - 2 phase UI */}
        <div style={{ marginTop: 24 }}>
          <h4>Video Evidence</h4>
          {accident.videoClipUrl ? (
            <video controls width="100%" style={{ maxWidth: 720, borderRadius: 8 }}>
              <source src={accident.videoClipUrl} type="video/mp4" />
              Your browser does not support video playback.
            </video>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 24, background: '#f5f5f5', borderRadius: 8 }}>
              <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
              <span style={{ color: '#666' }}>Đang trích xuất bằng chứng từ camera...</span>
            </div>
          )}
        </div>
      </Card>
    </>
  );
}
