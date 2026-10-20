import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { FileItem, DriveItem, DuplicateGroup } from '../types';
import { HardDrive, Folder, FileText, Search, Copy, Trash2, Eye, Plus, RefreshCw, AlertTriangle, Layers } from 'lucide-react';

export const FileExplorer: React.FC = () => {
  const [drives, setDrives] = useState<DriveItem[]>([]);
  const [currentPath, setCurrentPath] = useState<string>('C:\\');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<FileItem[] | null>(null);
  const [searching, setSearching] = useState<boolean>(false);

  // File Preview Modal
  const [previewFile, setPreviewFile] = useState<{ path: string; content: string } | null>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);

  // Duplicate Detection
  const [duplicates, setDuplicates] = useState<DuplicateGroup[] | null>(null);
  const [scanningDuplicates, setScanningDuplicates] = useState<boolean>(false);

  useEffect(() => {
    fetchDrives();
  }, []);

  useEffect(() => {
    if (currentPath) {
      loadDirectory(currentPath);
    }
  }, [currentPath]);

  const fetchDrives = async () => {
    try {
      const res = await api.getDrives();
      setDrives(res.drives);
      if (res.drives.length > 0 && !currentPath) {
        setCurrentPath(res.drives[0].mountpoint);
      }
    } catch (err: any) {
      console.error("Failed to load drives", err);
    }
  };

  const loadDirectory = async (path: string) => {
    try {
      setLoading(true);
      setError(null);
      setSearchResults(null);
      const res = await api.listFiles(path);
      setFiles(res.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to open directory '${path}'`);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      setSearching(true);
      const res = await api.searchDrives(searchQuery, currentPath);
      setSearchResults(res.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const handlePreview = async (filePath: string) => {
    try {
      setPreviewLoading(true);
      const res = await api.readFile(filePath);
      setPreviewFile(res);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to preview file');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDelete = async (filePath: string) => {
    if (!window.confirm(`Are you sure you want to delete '${filePath}'?`)) return;
    try {
      await api.deleteItem(filePath);
      loadDirectory(currentPath);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete file');
    }
  };

  const handleScanDuplicates = async () => {
    try {
      setScanningDuplicates(true);
      const res = await api.findDuplicates(currentPath);
      setDuplicates(res.duplicate_groups);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Duplicate scan failed');
    } finally {
      setScanningDuplicates(false);
    }
  };

  const displayedFiles = searchResults || files;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <HardDrive className="text-cyan-400" size={28} />
            Multi-Drive Filesystem Explorer
          </h1>
          <p className="text-slate-400 text-sm">
            Discover mounted drives, search across filesystems, preview documents, and detect duplicate files.
          </p>
        </div>
        <button
          onClick={handleScanDuplicates}
          disabled={scanningDuplicates}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium flex items-center gap-2 transition"
        >
          {scanningDuplicates ? <RefreshCw className="animate-spin" size={16} /> : <Layers size={16} />}
          Find Duplicates
        </button>
      </div>

      {/* Drive Selection Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {drives.map((d, idx) => (
          <button
            key={idx}
            onClick={() => setCurrentPath(d.mountpoint)}
            className={`p-4 rounded-xl border text-left transition flex items-start justify-between ${
              currentPath.startsWith(d.mountpoint)
                ? 'bg-cyan-950/40 border-cyan-500 text-cyan-200 shadow-lg shadow-cyan-950/40'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-850'
            }`}
          >
            <div>
              <div className="font-bold text-base flex items-center gap-2">
                <HardDrive size={18} className="text-cyan-400" />
                Drive {d.drive_letter}:
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {d.is_readable
                  ? `${(d.free_bytes / (1024 * 1024 * 1024)).toFixed(1)} GB free of ${(d.total_bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
                  : 'Inaccessible'}
              </div>
            </div>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
              {d.drive_type}
            </span>
          </button>
        ))}
      </div>

      {/* Path Breadcrumbs & Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 font-mono text-sm text-slate-200 w-full md:w-auto overflow-x-auto">
          <span className="text-cyan-400 font-bold">Path:</span>
          <input
            type="text"
            value={currentPath}
            onChange={(e) => setCurrentPath(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadDirectory(currentPath)}
            className="bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 w-full md:w-96 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <form onSubmit={handleSearch} className="flex gap-2 w-full md:w-auto">
          <input
            type="text"
            placeholder="Search filenames..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 w-full md:w-64"
          />
          <button
            type="submit"
            disabled={searching}
            className="px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium flex items-center gap-1 transition"
          >
            {searching ? <RefreshCw className="animate-spin" size={14} /> : <Search size={14} />}
            Search
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/50 border border-rose-500/50 rounded-lg text-rose-300 text-sm flex items-center gap-2">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Duplicate Results Modal */}
      {duplicates && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-slate-200 font-semibold text-base flex items-center gap-2">
              <Layers size={18} className="text-amber-400" />
              Detected Duplicate Groups ({duplicates.length})
            </h2>
            <button
              onClick={() => setDuplicates(null)}
              className="text-slate-400 hover:text-slate-200 text-xs"
            >
              Dismiss
            </button>
          </div>

          <div className="space-y-3 max-h-60 overflow-y-auto">
            {duplicates.map((group, idx) => (
              <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs space-y-1">
                <div className="font-bold text-slate-200 flex justify-between">
                  <span>Hash: {group.hash}</span>
                  <span className="text-amber-400">{(group.size_bytes / 1024).toFixed(1)} KB per file</span>
                </div>
                {group.files.map((f, i) => (
                  <div key={i} className="text-slate-400 font-mono pl-2">
                    • {f.path}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* File & Folder Listing */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center h-48">
            <RefreshCw className="animate-spin text-cyan-400" size={32} />
          </div>
        ) : (
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase text-xs">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Size</th>
                <th className="px-4 py-3">Modified</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {displayedFiles.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-850/50">
                  <td className="px-4 py-2.5 flex items-center gap-2 font-medium">
                    {item.is_dir ? (
                      <Folder className="text-amber-400" size={18} />
                    ) : (
                      <FileText className="text-cyan-400" size={18} />
                    )}
                    {item.is_dir ? (
                      <button
                        onClick={() => setCurrentPath(item.path)}
                        className="hover:underline text-slate-200 text-left"
                      >
                        {item.name}
                      </button>
                    ) : (
                      <span className="text-slate-200">{item.name}</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-400">
                    {item.is_dir ? '-' : `${(item.size_bytes / 1024).toFixed(1)} KB`}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-slate-400">
                    {new Date(item.modified_at * 1000).toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5 text-right space-x-2">
                    {!item.is_dir && (
                      <button
                        onClick={() => handlePreview(item.path)}
                        className="text-slate-400 hover:text-cyan-400 p-1"
                        title="Preview"
                      >
                        <Eye size={16} />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(item.path)}
                      className="text-slate-400 hover:text-rose-400 p-1"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Preview Modal */}
      {previewFile && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-3xl w-full space-y-4 max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-slate-200 font-mono text-sm">{previewFile.path}</h3>
              <button onClick={() => setPreviewFile(null)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>
            <pre className="bg-slate-950 p-4 rounded-lg text-xs font-mono text-slate-300 overflow-y-auto flex-1 whitespace-pre-wrap">
              {previewFile.content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
