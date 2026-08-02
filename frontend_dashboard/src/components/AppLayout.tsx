import { Layout, Menu, Button, Avatar, Space } from 'antd';
import { DashboardOutlined, VideoCameraOutlined, WarningOutlined, BellOutlined, LogoutOutlined, UserOutlined } from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';

const { Sider, Content, Header } = Layout;

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/cameras', icon: <VideoCameraOutlined />, label: 'Cameras' },
  { key: '/accidents', icon: <WarningOutlined />, label: 'Accidents' },
  { key: '/alerts', icon: <BellOutlined />, label: 'Alerts' },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider>
        <div style={{ color: '#fff', textAlign: 'center', padding: '16px', fontWeight: 'bold' }}>
          🚨 Accident Detection
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 'bold', fontSize: 18 }}>Accident Detection System</span>
          <Space>
            <Avatar icon={<UserOutlined />} size="small" />
            <span>{user.name || user.email || ''}</span>
            <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout}>
              Logout
            </Button>
          </Space>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
