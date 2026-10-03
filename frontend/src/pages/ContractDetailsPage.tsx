
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import StatusBadge from '../components/StatusBadge';
import { getContractById } from '../services/contractService';
import type { Contract } from '../types/contract';

function ContractDetailsPage() {
  const { id } = useParams<{ id: string }>();

  const [contract, setContract] = useState<Contract | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadContract = async () => {
      if (!id) {
        setLoading(false);
        return;
      }

      const data = await getContractById(id);
      setContract(data);
      setLoading(false);
    };

    loadContract();
  }, [id]);

  if (loading) {
    return <p>جاري تحميل تفاصيل العقد...</p>;
  }

  if (!contract) {
    return (
      <div>
        <h2>العقد غير موجود</h2>

        <Link to="/contracts">
          العودة إلى قائمة العقود
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h2>تفاصيل العقد</h2>

      <div
        style={{
          marginTop: '20px',
          lineHeight: '1.8'
        }}
      >
        <p>
          <strong>اسم العقد:</strong> {contract.name}
        </p>

        <p>
          <strong>نوع الملف:</strong> {contract.fileType}
        </p>

        <p>
          <strong>تاريخ الرفع:</strong> {contract.uploadDate}
        </p>

        <p>
          <strong>الحالة:</strong>{' '}
          <StatusBadge status={contract.status} />
        </p>

        <p>
          <strong>تاريخ البداية:</strong> {contract.startDate}
        </p>

        <p>
          <strong>تاريخ الانتهاء:</strong> {contract.endDate}
        </p>

        <p>
          <strong>الأطراف:</strong> {contract.parties}
        </p>

        <p>
          <strong>قيمة العقد:</strong> {contract.value}
        </p>
      </div>

      <div style={{ marginTop: '30px' }}>
        <Link
          to={`/chat/${contract.id}`}
          style={{
            padding: '8px 16px',
            backgroundColor: '#2563eb',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '4px',
            marginRight: '10px'
          }}
        >
          فتح الشات
        </Link>

        <Link
          to="/contracts"
          style={{
            padding: '8px 16px',
            backgroundColor: '#6b7280',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '4px'
          }}
        >
          رجوع للقائمة
        </Link>
      </div>
    </div>
  );
}

export default ContractDetailsPage;