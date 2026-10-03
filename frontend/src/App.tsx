
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';

import UploadPage from './pages/UploadPage';
import ContractsListPage from './pages/ContractsListPage';
import ContractDetailsPage from './pages/ContractDetailsPage';
import ChatPage from './pages/ChatPage';

function App() {
  return (
    <BrowserRouter>
      <div
        style={{
          fontFamily: 'Arial, sans-serif',
          padding: '20px',
          maxWidth: '1000px',
          margin: '0 auto'
        }}
      >
        <h1
          style={{
            marginBottom: '25px'
          }}
        >
          AI Legal Contract Management System
        </h1>

        {/* قائمة التنقل الرئيسية */}
        <nav
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '30px',
            padding: '10px',
            backgroundColor: '#f3f4f6',
            borderRadius: '8px',
            border: '1px solid #e5e7eb'
          }}
        >
          {/* أقصى اليسار */}
          <Link
            to="/contracts"
            style={{
              padding: '10px 18px',
              textDecoration: 'none',
              color: '#2563eb',
              backgroundColor: '#ffffff',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontWeight: 'bold'
            }}
          >
            قائمة العقود
          </Link>

          {/* أقصى اليمين */}
          <Link
            to="/"
            style={{
              padding: '10px 18px',
              textDecoration: 'none',
              color: '#2563eb',
              backgroundColor: '#ffffff',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontWeight: 'bold'
            }}
          >
            رفع عقد
          </Link>
        </nav>

        {/* الصفحات */}
        <Routes>
          <Route
            path="/"
            element={<UploadPage />}
          />

          <Route
            path="/contracts"
            element={<ContractsListPage />}
          />

          <Route
            path="/contracts/:id"
            element={<ContractDetailsPage />}
          />

          <Route
            path="/chat/:id"
            element={<ChatPage />}
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
