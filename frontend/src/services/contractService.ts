import type { Contract, ContractStatus } from '../types/contract';

const API_BASE_URL = 'http://127.0.0.1:8000';

interface BackendContract {
  contract_id: string;
  name: string;
  file_type: string;
  uploaded_at: string;
  status: string;
  start_date?: string | null;
  end_date?: string | null;
  ingestion_status?: string;
}

interface ContractsResponse {
  contracts: BackendContract[];
}

const mapContract = (contract: BackendContract): Contract => {
  let status: ContractStatus = 'Active';

  if (contract.status === 'Expiring Soon') {
    status = 'Expiring Soon';
  } else if (contract.status === 'Expired') {
    status = 'Expired';
  }

  return {
    id: contract.contract_id,
    name: contract.name,
    fileType: contract.file_type,
    uploadDate: contract.uploaded_at
      ? contract.uploaded_at.split('T')[0]
      : '',
    status: status,
    startDate: contract.start_date ?? undefined,
    endDate: contract.end_date ?? undefined,
  };
};

export const getContracts = async (): Promise<Contract[]> => {
  const url = API_BASE_URL + '/api/contracts';

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('فشل في جلب العقود');
  }

  const data: ContractsResponse = await response.json();

  return data.contracts.map(mapContract);
};

export const getContractById = async (
  id: string
): Promise<Contract | undefined> => {
  const url = API_BASE_URL + '/api/contracts/' + id;

  const response = await fetch(url);

  if (response.status === 404) {
    return undefined;
  }

  if (!response.ok) {
    throw new Error('فشل في جلب العقد');
  }

  const data: BackendContract = await response.json();

  return mapContract(data);
};

export const uploadContract = async (
  file: File
): Promise<{ success: boolean; message: string }> => {
  const formData = new FormData();

  formData.append('file', file);

  const url = API_BASE_URL + '/api/contracts/upload';

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let message = 'فشل رفع العقد';

    try {
      const errorData = await response.json();

      if (errorData && errorData.detail) {
        message = errorData.detail;
      }
    } catch {
      // استخدام الرسالة الافتراضية
    }

    throw new Error(message);
  }

  const data = await response.json();

  return {
    success: true,
    message:
      data.message ||
      'تم رفع العقد بنجاح: ' + file.name,
  };
};

export const deleteContract = async (
  id: string
): Promise<void> => {
  const url = API_BASE_URL + '/api/contracts/' + id;

  const response = await fetch(url, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('فشل حذف العقد');
  }
};