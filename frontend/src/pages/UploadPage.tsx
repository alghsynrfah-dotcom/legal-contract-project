import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { uploadContract } from '../services/contractService';

function UploadPage() {
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];

    if (file) {
      setSelectedFile(file);
      setMessage('');
      setSuccess(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage('الرجاء اختيار ملف أولاً');
      setSuccess(false);
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const result = await uploadContract(selectedFile);

      setMessage(result.message);
      setSuccess(result.success);

      if (result.success) {
        setTimeout(() => {
          navigate('/contracts');
        }, 700);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : 'حدث خطأ أثناء رفع العقد';

      setMessage(errorMessage);
      setSuccess(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>رفع عقد جديد</h2>

      <div style={{ marginTop: '20px' }}>
        <input
          type="file"
          accept=".pdf,.doc,.docx"
          onChange={handleFileChange}
        />
      </div>

      {selectedFile && (
        <p style={{ marginTop: '15px' }}>
          <strong>الملف المختار:</strong>{' '}
          {selectedFile.name}
        </p>
      )}

      <div style={{ marginTop: '15px' }}>
        <button
          onClick={handleUpload}
          disabled={loading}
          style={{
            padding: '8px 16px',
            backgroundColor: loading ? '#9ca3af' : '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'جاري الرفع...' : 'رفع العقد'}
        </button>
      </div>

      {message && (
        <p
          style={{
            marginTop: '15px',
            color: success ? '#16a34a' : '#dc2626'
          }}
        >
          {message}
        </p>
      )}
    </div>
  );
}

export default UploadPage;
