import { Layout, Menu } from 'antd';
import { DashboardOutlined, VideoCameraOutlined, WarningOutlined, BellOutlined } from '@ant-design/icons';
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

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider>
        <div style={{ color: '#fff', textAlign: 'center', padding: '16px', fontWeight: 'bold' }}>
          Accident Detection
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', fontWeight: 'bold', fontSize: 18 }}>
          Accident Detection System
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
