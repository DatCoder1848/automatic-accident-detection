import { Table, Button, Modal, Form, Input, Select, Tag, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import api from '../api/client';

export default function Cameras() {
  const [open, setOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: cameras = [], isLoading } = useQuery({ queryKey: ['cameras'], queryFn: () => api.get('/cameras').then(r => r.data) });

  const save = useMutation({
    mutationFn: (values: any) => editId ? api.patch(`/cameras/${editId}`, values) : api.post('/cameras', values),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['cameras'] }); setOpen(false); form.resetFields(); setEditId(null); },
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/cameras/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cameras'] }),
  });

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Location', dataIndex: 'location', key: 'location' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={s === 'ACTIVE' ? 'green' : s === 'MAINTENANCE' ? 'orange' : 'red'}>{s}</Tag> },
    { title: 'Actions', key: 'actions', render: (_: any, record: any) => (
      <Space>
        <a onClick={() => { setEditId(record.id); form.setFieldsValue(record); setOpen(true); }}>Edit</a>
        <a onClick={() => remove.mutate(record.id)}>Delete</a>
      </Space>
    )},
  ];

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditId(null); form.resetFields(); setOpen(true); }} style={{ marginBottom: 16 }}>
        Add Camera
      </Button>
      <Table dataSource={cameras} columns={columns} rowKey="id" loading={isLoading} />
      <Modal title={editId ? 'Edit Camera' : 'Add Camera'} open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={(v) => save.mutate(v)}>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="location" label="Location" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="streamUrl" label="Stream URL" rules={[{ required: !editId }]}><Input /></Form.Item>
          <Form.Item name="status" label="Status" initialValue="ACTIVE">
            <Select options={[{ value: 'ACTIVE' }, { value: 'INACTIVE' }, { value: 'MAINTENANCE' }]} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
