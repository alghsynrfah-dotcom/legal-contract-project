export type ContractStatus = 'Active' | 'Expiring Soon' | 'Expired';

export interface Contract {
  id: string;
  name: string;
  fileType: string;
  uploadDate: string;
  status: ContractStatus;
  startDate?: string;
  endDate?: string;
  parties?: string;
  value?: string;
}