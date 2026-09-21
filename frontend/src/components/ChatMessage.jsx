import { User, Bot, CreditCard, Landmark, PiggyBank, AlertCircle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const AGENT_CONFIG = {
  super_agent: { label: 'SmartBank AI', color: 'bg-blue-100 text-blue-700', icon: Bot },
  loan_agent: { label: 'Loan Specialist', color: 'bg-green-100 text-green-700', icon: PiggyBank },
  account_agent: { label: 'Account Specialist', color: 'bg-purple-100 text-purple-700', icon: Landmark },
  card_agent: { label: 'Card Specialist', color: 'bg-orange-100 text-orange-700', icon: CreditCard },
  complaint_agent: { label: 'Complaint Desk', color: 'bg-red-100 text-red-700', icon: AlertCircle },
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const agent = AGENT_CONFIG[message.agent_name] || AGENT_CONFIG.super_agent

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-bank-100 flex items-center justify-center flex-shrink-0 mt-1">
          <agent.icon className="w-4 h-4 text-bank-600" />
        </div>
      )}

      <div className={`max-w-[70%] ${isUser ? 'order-first' : ''}`}>
        {!isUser && message.agent_name && (
          <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full mb-1 ${agent.color}`}>
            {agent.label}
          </span>
        )}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-bank-600 text-white rounded-br-md'
              : 'bg-gray-100 text-gray-800 rounded-bl-md markdown-body'
          }`}
        >
          {isUser ? message.content : <ReactMarkdown>{message.content}</ReactMarkdown>}
        </div>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-bank-600 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="w-4 h-4 text-white" />
        </div>
      )}
    </div>
  )
}
