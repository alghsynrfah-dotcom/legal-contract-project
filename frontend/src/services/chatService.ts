
export interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
}

export interface Source {
  contract_name: string;
  page: number | null;
  chunk: string;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  tools_used: string[];
  sources: Source[];
}

const API_BASE_URL = 'http://localhost:8000/api';

export const sendMessage = async (
  contractId: string,
  message: string,
  sessionId?: string
): Promise<ChatResponse> => {
  const url = API_BASE_URL + '/agent/chat';

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      contract_id: contractId,
      message: message,
      session_id: sessionId ?? null,
    }),
  });

  if (!response.ok) {
    let errorMessage = 'حدث خطأ أثناء الاتصال بالـ Agent.';

    try {
      const errorData = await response.json();

      if (
        errorData &&
        errorData.error &&
        errorData.error.message
      ) {
        errorMessage = errorData.error.message;
      }
    } catch {
      // الرد ليس JSON
    }

    throw new Error(errorMessage);
  }

  return response.json();
};
