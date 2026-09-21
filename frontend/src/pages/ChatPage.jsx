import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { chatAPI, agentAPI } from '../services/api'
import Sidebar from '../components/Sidebar'
import ChatMessage from '../components/ChatMessage'
import ChatInput from '../components/ChatInput'
import AgentPanel from '../components/AgentPanel'
import { PanelRightOpen, PanelRightClose, Loader2 } from 'lucide-react'

const DEMO_CUSTOMER_ID = 1

export default function ChatPage() {
  const { user, logout } = useAuth()
  const [threads, setThreads] = useState([])
  const [activeThread, setActiveThread] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [showPanel, setShowPanel] = useState(true)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    loadThreads()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadThreads = async () => {
    try {
      const res = await chatAPI.getThreads(DEMO_CUSTOMER_ID)
      setThreads(res.data.threads)
    } catch (err) {
      console.error('Failed to load threads:', err)
    }
  }

  const selectThread = async (thread) => {
    setActiveThread(thread)
    try {
      const res = await chatAPI.getMessages(thread.id)
      setMessages(res.data.messages)
    } catch (err) {
      console.error('Failed to load messages:', err)
    }
  }

  const newThread = () => {
    setActiveThread(null)
    setMessages([])
  }

  const sendMessage = async (text) => {
    const userMsg = { role: 'user', content: text, agent_name: null }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await chatAPI.sendMessage({
        message: text,
        thread_id: activeThread?.id || null,
        customer_id: DEMO_CUSTOMER_ID,
      })

      const assistantMsg = {
        role: 'assistant',
        content: res.data.reply,
        agent_name: res.data.agent,
      }
      setMessages((prev) => [...prev, assistantMsg])

      if (!activeThread) {
        setActiveThread({ id: res.data.thread_id, title: text.slice(0, 50) })
        loadThreads()
      }
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
        agent_name: 'super_agent',
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-white">
      <Sidebar
        threads={threads}
        activeThread={activeThread}
        onSelectThread={selectThread}
        onNewThread={newThread}
        onLogout={logout}
      />

      <div className="flex-1 flex flex-col">
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-white">
          <div>
            <h2 className="font-semibold text-gray-800">
              {activeThread ? activeThread.title : 'New Conversation'}
            </h2>
            <p className="text-xs text-gray-500">
              Powered by multi-agent AI system
            </p>
          </div>
          <button
            onClick={() => setShowPanel(!showPanel)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition"
          >
            {showPanel ? <PanelRightClose className="w-5 h-5" /> : <PanelRightOpen className="w-5 h-5" />}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="text-center mt-20">
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  Welcome to SmartBank AI
                </h3>
                <p className="text-gray-500 mb-6">
                  I can help you with accounts, loans, cards, and complaints.
                </p>
                <div className="grid grid-cols-2 gap-3 max-w-md mx-auto">
                  {[
                    'What is my account balance?',
                    'Check my loan eligibility',
                    'Show my credit card details',
                    'I want to file a complaint',
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => sendMessage(q)}
                      className="px-4 py-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-xl text-sm text-gray-700 text-left transition"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <ChatMessage key={i} message={msg} />
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Agent is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <ChatInput onSend={sendMessage} disabled={loading} />
      </div>

      {showPanel && <AgentPanel threadId={activeThread?.id} />}
    </div>
  )
}
