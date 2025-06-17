import React, { useState } from 'react';
import { Tabs, Tab } from '@mui/material';
import UserManagement from '../components/admin/UserManagement';
import ModelManagement from '../components/admin/ModelManagement';
import FAISSDashboard from '../components/admin/FAISSDashboard';

const AdminPage = () => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <div>
      <Tabs value={activeTab} onChange={handleTabChange}>
        <Tab label="Users" />
        <Tab label="Models" />
        <Tab label="FAISS Index" />
      </Tabs>

      {activeTab === 0 && <UserManagement />}
      {activeTab === 1 && <ModelManagement />}
      {activeTab === 2 && <FAISSDashboard />}
    </div>
  );
};

export default AdminPage; 