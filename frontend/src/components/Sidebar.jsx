import { MessageSquarePlus, MessageSquare, LogOut, Building2 } from 'lucide-react'

export default function Sidebar({ threads, activeThread, onSelectThread, onNewThread, onLogout }) {
  return (
    <div className="w-72 bg-gray-900 text-white flex flex-col h-full">
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="w-6 h-6 text-blue-400" />
          <span className="font-bold text-lg">SmartBank AI</span>
        </div>
        <button
          onClick={onNewThread}
          className="w-full flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-lg transition text-sm font-medium"
        >
          <MessageSquarePlus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-1">
        {threads.map((thread) => (
          <button
            key={thread.id}
            onClick={() => onSelectThread(thread)}
            className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm text-left transition ${
              activeThread?.id === thread.id
                ? 'bg-gray-700 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            }`}
          >
            <MessageSquare className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">{thread.title || 'New Chat'}</span>
          </button>
        ))}
      </div>

      <div className="p-4 border-t border-gray-700">
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-2 px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition text-sm"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </div>
  )
}
