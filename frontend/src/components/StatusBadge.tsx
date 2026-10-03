import type { ContractStatus } from '../types/contract';

interface StatusBadgeProps {
  status: ContractStatus;
}

function StatusBadge({ status }: StatusBadgeProps) {
  const getStatusColor = () => {
    if (status === 'Active') {
      return '#16a34a';
    }

    if (status === 'Expiring Soon') {
      return '#ca8a04';
    }

    return '#dc2626';
  };

  return (
    <span
      style={{
        color: getStatusColor(),
        fontWeight: 'bold'
      }}
    >
      {status}
    </span>
  );
}

export default StatusBadge;