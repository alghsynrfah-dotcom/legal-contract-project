import { Link } from 'react-router-dom';
import type { Contract } from '../types/contract';
import StatusBadge from './StatusBadge';

interface ContractCardProps {
  contract: Contract;
}

function ContractCard({ contract }: ContractCardProps) {
  return (
    <div
      style={{
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '12px',
        backgroundColor: '#fff'
      }}
    >
      <h3>{contract.name}</h3>

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

      <div style={{ marginTop: '12px' }}>
        <Link
          to={`/contracts/${contract.id}`}
          style={{
            color: '#2563eb',
            marginRight: '15px'
          }}
        >
          التفاصيل
        </Link>

        <Link
          to={`/chat/${contract.id}`}
          style={{
            color: '#2563eb'
          }}
        >
          شات
        </Link>
      </div>
    </div>
  );
}

export default ContractCard;