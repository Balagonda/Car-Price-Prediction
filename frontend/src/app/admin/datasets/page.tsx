"use client";

import { useState } from "react";
import { uploadDataset } from "@/lib/admin";
import { useMutation } from "@tanstack/react-query";
import type { DatasetUploadResponse } from "@/lib/admin";

export default function DatasetManagementPage() {
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<"replace" | "merge">("replace");
  const [version, setVersion] = useState<string>("v1.0");
  const [result, setResult] = useState<DatasetUploadResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("Please select a CSV file.");
      return uploadDataset(file, mode, version);
    },
    onSuccess: (data) => {
      setResult(data);
      setErrorMsg(null);
      setFile(null); // reset file
    },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onError: (error: any) => {
      setErrorMsg(error?.response?.data?.detail?.message || error.message || "Upload failed");
      setResult(null);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg("Please select a CSV file first.");
      return;
    }
    uploadMutation.mutate();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header>
        <h1 className="text-3xl font-bold text-white tracking-tight">Dataset Management</h1>
        <p className="text-zinc-400 mt-1">Upload and manage historical car datasets for model training.</p>
      </header>

      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Upload CSV Dataset</label>
            <div className="flex items-center justify-center w-full">
                <label className="flex flex-col items-center justify-center w-full h-40 border-2 border-zinc-700 border-dashed rounded-xl cursor-pointer bg-zinc-800/30 hover:bg-zinc-800/60 hover:border-indigo-500/50 transition-all">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <svg className="w-8 h-8 mb-3 text-zinc-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                            <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/>
                        </svg>
                        <p className="mb-2 text-sm text-zinc-400"><span className="font-semibold text-indigo-400">Click to upload</span> or drag and drop</p>
                        <p className="text-xs text-zinc-500">CSV file containing vehicle data</p>
                        {file && (
                          <p className="mt-2 text-sm font-medium text-emerald-400">Selected: {file.name}</p>
                        )}
                    </div>
                    <input 
                      type="file" 
                      className="hidden" 
                      accept=".csv"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                    />
                </label>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Version Tag</label>
              <input 
                type="text" 
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                placeholder="e.g. v2.1"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Import Strategy</label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="radio" 
                    name="mode" 
                    value="replace" 
                    checked={mode === "replace"} 
                    onChange={() => setMode("replace")}
                    className="text-indigo-500 focus:ring-indigo-500/50 bg-zinc-950 border-zinc-700" 
                  />
                  <span className="text-zinc-300">Replace (Clear old)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="radio" 
                    name="mode" 
                    value="merge" 
                    checked={mode === "merge"} 
                    onChange={() => setMode("merge")}
                    className="text-indigo-500 focus:ring-indigo-500/50 bg-zinc-950 border-zinc-700" 
                  />
                  <span className="text-zinc-300">Merge (Append)</span>
                </label>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={uploadMutation.isPending}
            className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white font-medium py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(99,102,241,0.2)] disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {uploadMutation.isPending ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Processing...
              </>
            ) : "Upload & Process Dataset"}
          </button>
        </form>

        {errorMsg && (
          <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
            <p className="text-sm text-red-400 font-medium">⚠️ {errorMsg}</p>
          </div>
        )}

        {result && (
          <div className="mt-6 p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-xl space-y-3">
            <h3 className="text-emerald-400 font-medium flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
              {result.message}
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-zinc-300">
              <div><span className="text-zinc-500 block">Rows:</span> {result.row_count}</div>
              <div><span className="text-zinc-500 block">Columns:</span> {result.column_count}</div>
              <div><span className="text-zinc-500 block">Duplicates Removed:</span> {result.duplicate_rows_removed}</div>
              <div><span className="text-zinc-500 block">Invalid Rows:</span> {result.invalid_rows_removed}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
