
import { useEffect, useState } from 'react';

import ContractCard from '../components/ContractCard';
import { getContracts } from '../services/contractService';
import type { Contract } from '../types/contract';

function ContractsListPage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadContracts = async () => {
      try {
        const data = await getContracts();
        setContracts(data);
      } finally {
        setLoading(false);
      }
    };

    loadContracts();
  }, []);

  const filteredContracts = contracts.filter((contract) => {
    const search = searchTerm.toLowerCase();

    return (
      contract.name.toLowerCase().includes(search) ||
      contract.fileType.toLowerCase().includes(search) ||
      contract.status.toLowerCase().includes(search)
    );
  });

  if (loading) {
    return <p>جاري تحميل العقود...</p>;
  }

  return (
    <div>
      <h2>قائمة العقود</h2>

      <div style={{ margin: '20px 0' }}>
        <input
          type="text"
          placeholder="ابحث باسم العقد أو نوع الملف أو الحالة..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            padding: '8px 12px',
            width: '350px',
            border: '1px solid #ccc',
            borderRadius: '4px'
          }}
        />
      </div>

      {filteredContracts.length === 0 ? (
        <p
          style={{
            marginTop: '20px',
            color: '#666'
          }}
        >
          لا توجد عقود مطابقة للبحث
        </p>
      ) : (
        <div>
          {filteredContracts.map((contract) => (
            <ContractCard
              key={contract.id}
              contract={contract}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default ContractsListPage;
