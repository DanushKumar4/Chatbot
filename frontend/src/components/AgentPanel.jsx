import { useState, useEffect } from 'react'
import { agentAPI } from '../services/api'
import { Activity, Route, Wrench, CheckCircle, XCircle, Clock, ChevronRight } from 'lucide-react'

export default function AgentPanel({ threadId }) {
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState(null)
  const [tab, setTab] = useState('activity')

  useEffect(() => {
    if (!threadId) return
    agentAPI.getLogs(threadId).then((res) => setLogs(res.data.logs))
  }, [threadId])

  useEffect(() => {
    agentAPI.getStats().then((res) => setStats(res.data)).catch(() => {})
  }, [])

  const actionIcon = (action) => {
    switch (action) {
      case 'routing': return <Route className="w-3.5 h-3.5 text-blue-500" />
      case 'routed': return <ChevronRight className="w-3.5 h-3.5 text-green-500" />
      case 'tool_call': return <Wrench className="w-3.5 h-3.5 text-orange-500" />
      case 'completed': return <CheckCircle className="w-3.5 h-3.5 text-green-500" />
      case 'started': return <Clock className="w-3.5 h-3.5 text-blue-500" />
      default: return <Activity className="w-3.5 h-3.5 text-gray-500" />
    }
  }

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col h-full">
      <div className="p-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-800 flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Agent Monitor
        </h3>
        <div className="flex gap-1 mt-3">
          <button
            onClick={() => setTab('activity')}
            className={`px-3 py-1 text-xs rounded-full font-medium transition ${
              tab === 'activity' ? 'bg-bank-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Activity
          </button>
          <button
            onClick={() => setTab('stats')}
            className={`px-3 py-1 text-xs rounded-full font-medium transition ${
              tab === 'stats' ? 'bg-bank-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Stats
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-3">
        {tab === 'activity' && (
          <div className="space-y-2">
            {logs.length === 0 && (
              <p className="text-sm text-gray-400 text-center mt-8">No activity yet</p>
            )}
            {logs.map((log, i) => (
              <div key={i} className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg">
                <div className="mt-0.5">{actionIcon(log.action)}</div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-gray-700">{log.agent_name}</span>
                    <span className="text-xs text-gray-400">{log.action}</span>
                  </div>
                  {log.detail && (
                    <p className="text-xs text-gray-500 mt-0.5 truncate">
                      {log.detail.tool && `Tool: ${log.detail.tool}`}
                      {log.detail.target && `→ ${log.detail.target}`}
                      {log.detail.reason && ` (${log.detail.reason})`}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === 'stats' && stats && (
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Runs</h4>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center">
                  <div className="text-xl font-bold text-gray-800">{stats.run_stats?.total || 0}</div>
                  <div className="text-xs text-gray-500">Total</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-green-600">{stats.run_stats?.succeeded || 0}</div>
                  <div className="text-xs text-gray-500">Succeeded</div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-3">
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Agent Usage</h4>
              {Object.entries(stats.agent_stats || {}).map(([agent, data]) => (
                <div key={agent} className="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0">
                  <span className="text-xs font-medium text-gray-700">{agent}</span>
                  <span className="text-xs text-gray-500">{data.total_actions} actions</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
