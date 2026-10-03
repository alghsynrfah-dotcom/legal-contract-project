
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { sendMessage } from '../services/chatService';

interface Source {
  contract_name: string;
  page: number | null;
  chunk: string;
}

interface Message {
  role: 'user' | 'ai';
  text: string;
  toolsUsed?: string[];
  sources?: Source[];
}

function ChatPage() {
  const { id } = useParams<{ id: string }>();

  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      text: 'مرحباً، أنا المساعد الذكي. كيف يمكنني مساعدتك بخصوص هذا العقد؟',
    },
  ]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // حفظ Session ID حتى يستمر الـ Agent بتذكر المحادثة
  const [sessionId, setSessionId] = useState<string | undefined>();

  const handleSend = async () => {
    if (!input.trim() || !id || loading) {
      return;
    }

    const userText = input.trim();

    const userMessage: Message = {
      role: 'user',
      text: userText,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendMessage(
        id,
        userText,
        sessionId
      );

      // حفظ Session ID الذي أعاده الـ Backend
      setSessionId(response.session_id);

      const aiMessage: Message = {
        role: 'ai',
        text: response.answer,
        toolsUsed: response.tools_used,
        sources: response.sources,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : 'حدث خطأ أثناء معالجة السؤال.';

      setMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          text: errorMessage,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>

      <h2>الشات - عقد رقم {id}</h2>

      <div style={{ marginBottom: '15px' }}>
        <Link
          to={`/contracts/${id}`}
          style={{
            color: '#2563eb',
            textDecoration: 'none',
          }}
        >
          ← رجوع لتفاصيل العقد
        </Link>
      </div>

      {/* صندوق الرسائل */}
      <div
        style={{
          border: '1px solid #ddd',
          borderRadius: '8px',
          padding: '15px',
          height: '500px',
          overflowY: 'auto',
          backgroundColor: '#f9fafb',
          marginBottom: '15px',
        }}
      >

        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              marginBottom: '20px',
              textAlign:
                msg.role === 'user'
                  ? 'left'
                  : 'right',
            }}
          >

            {/* الرسالة */}
            <div
              style={{
                display: 'inline-block',
                padding: '10px 14px',
                borderRadius: '12px',
                backgroundColor:
                  msg.role === 'user'
                    ? '#2563eb'
                    : '#e5e7eb',
                color:
                  msg.role === 'user'
                    ? 'white'
                    : '#111',
                maxWidth: '70%',
                textAlign: 'right',
              }}
            >
              {msg.text}
            </div>

            {/* معلومات الـ Agent */}
            {msg.role === 'ai' && (
              <div
                style={{
                  marginTop: '8px',
                  padding: '10px',
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  fontSize: '14px',
                  textAlign: 'right',
                }}
              >

                {/* الأدوات المستخدمة */}
                {msg.toolsUsed &&
                  msg.toolsUsed.length > 0 && (
                    <div style={{ marginBottom: '8px' }}>

                      <strong>
                        الأدوات المستخدمة:
                      </strong>

                      <ul style={{ margin: '5px 0' }}>
                        {msg.toolsUsed.map(
                          (tool, toolIndex) => (
                            <li key={toolIndex}>
                              {tool}
                            </li>
                          )
                        )}
                      </ul>

                    </div>
                  )}

                {/* المصادر */}
                {msg.sources &&
                  msg.sources.length > 0 && (
                    <div style={{ marginBottom: '8px' }}>

                      <strong>
                        المصادر:
                      </strong>

                      <ul style={{ margin: '5px 0' }}>
                        {msg.sources.map(
                          (source, sourceIndex) => (
                            <li
                              key={sourceIndex}
                              style={{
                                marginBottom: '10px',
                              }}
                            >
                              <div>
                                <strong>
                                  {source.contract_name}
                                </strong>
                              </div>

                              {source.page !== null && (
                                <div
                                  style={{
                                    color: '#666',
                                    marginTop: '3px',
                                  }}
                                >
                                  الصفحة: {source.page}
                                </div>
                              )}

                              <div
                                style={{
                                  marginTop: '5px',
                                  color: '#444',
                                  lineHeight: '1.6',
                                }}
                              >
                                {source.chunk}
                              </div>
                            </li>
                          )
                        )}
                      </ul>

                    </div>
                  )}

              </div>
            )}

          </div>
        ))}

        {/* Loading */}
        {loading && (
          <div
            style={{
              textAlign: 'right',
              color: '#666',
              marginTop: '10px',
            }}
          >
            جاري معالجة السؤال...
          </div>
        )}

      </div>

      {/* إدخال السؤال */}
      <div
        style={{
          display: 'flex',
          gap: '10px',
        }}
      >

        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleSend();
            }
          }}
          placeholder="اكتب سؤالك عن العقد..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '12px',
            border: '1px solid #ccc',
            borderRadius: '8px',
            fontSize: '16px',
          }}
        />

        <button
          onClick={handleSend}
          disabled={
            loading || !input.trim()
          }
          style={{
            padding: '12px 20px',
            border: 'none',
            borderRadius: '8px',
            backgroundColor:
              loading
                ? '#9ca3af'
                : '#2563eb',
            color: 'white',
            cursor:
              loading
                ? 'not-allowed'
                : 'pointer',
            fontSize: '16px',
          }}
        >
          {loading
            ? 'جاري...'
            : 'إرسال'}
        </button>

      </div>

    </div>
  );
}

export default ChatPage;
