import React from 'react';

export function AuditLogsTab({ logs, loading, error }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">Security & Audit Logs</h2>
          <p className="text-sm text-gray-500">Transparent logs of all AI negotiations, profit margins, and strict bounds enforcement.</p>
        </div>
      </div>
      {loading ? <p>Loading logs...</p> : error ? <p className="text-red-500">{error}</p> : logs.length === 0 ? <p className="text-gray-400">No audit logs found yet.</p> : (
        <div className="grid md:grid-cols-2 gap-6">
          {logs.map((log) => (
            <div key={log._id} className="bg-gray-100 p-5 rounded-lg text-sm border-l-4 border-black">
              <div className="flex justify-between items-start mb-3">
                <span className="font-bold text-black uppercase tracking-wider bg-white px-2 py-1 rounded text-xs">{log.action}</span>
                <span className="text-xs text-gray-500 font-medium">{new Date(log.timestamp).toLocaleString()}</span>
              </div>
              <p className="text-gray-800 mb-3 bg-white p-3 rounded"><strong>Reasoning:</strong><br />{log.reason}</p>
              <p className="text-green-700 font-bold mb-2 text-base">{log.result}</p>
              {log.metadata?.products && log.metadata.products.length > 0 && (
                <div className="mt-4 bg-white p-3 rounded border border-gray-200">
                  <p className="text-xs font-bold text-gray-500 uppercase mb-2">Products in Discussion</p>
                  <div className="flex flex-col gap-2">
                    {log.metadata.products.map((p, idx) => (
                      <div key={idx} className="flex items-center gap-3">
                        <img src={p.image_url} alt={p.name} className="w-10 h-10 rounded object-cover border" />
                        <div><p className="text-sm font-semibold line-clamp-1">{p.name}</p><p className="text-xs text-gray-500">₹{p.price}</p></div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {log.user_id && <p className="text-xs text-gray-400 mt-4 text-right">User ID: {log.user_id}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
