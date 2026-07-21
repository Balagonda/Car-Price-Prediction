"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getModels, trainModel, activateModel } from "@/lib/admin";

export default function ModelsManagementPage() {
  const queryClient = useQueryClient();
  const [datasetPath, setDatasetPath] = useState<string>("data/datasets/latest.csv");
  const [versionTag, setVersionTag] = useState<string>("v3.0");
  const [trainStatus, setTrainStatus] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { data: models, isLoading } = useQuery({
    queryKey: ["admin", "models"],
    queryFn: getModels,
    refetchInterval: 10000, // refresh often to see training status changes
  });

  const trainMutation = useMutation({
    mutationFn: () => trainModel(datasetPath, versionTag),
    onSuccess: (data) => {
      setTrainStatus(data.status);
      setErrorMsg(null);
      // Let polling pick up the new "training" version
    },
    onError: (error: any) => {
      setErrorMsg(error?.response?.data?.detail?.message || error.message || "Training trigger failed");
    }
  });

  const activateMutation = useMutation({
    mutationFn: (versionId: string) => activateModel(versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "models"] });
    },
    onError: (error: any) => {
      alert("Failed to activate: " + (error?.response?.data?.detail?.message || error.message));
    }
  });

  const handleTrain = (e: React.FormEvent) => {
    e.preventDefault();
    trainMutation.mutate();
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header>
        <h1 className="text-3xl font-bold text-white tracking-tight">Model Governance</h1>
        <p className="text-zinc-400 mt-1">Manage ML model versions, trigger training, and control active deployments.</p>
      </header>

      {/* Trigger Training Section */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl">
        <h2 className="text-xl font-semibold text-zinc-100 mb-4">Manual Model Training</h2>
        <form onSubmit={handleTrain} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Dataset Path (Server Local)</label>
            <input 
              type="text" 
              value={datasetPath}
              onChange={(e) => setDatasetPath(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">New Version Tag</label>
            <input 
              type="text" 
              value={versionTag}
              onChange={(e) => setVersionTag(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              placeholder="vX.X"
              required
            />
          </div>
          <button
            type="submit"
            disabled={trainMutation.isPending}
            className="w-full bg-indigo-500 hover:bg-indigo-400 text-white font-medium py-3 rounded-xl transition-all disabled:opacity-50 flex items-center justify-center h-[50px]"
          >
            {trainMutation.isPending ? "Starting..." : "Run Pipeline"}
          </button>
        </form>
        {errorMsg && <p className="text-red-400 text-sm mt-4">⚠️ {errorMsg}</p>}
        {trainStatus === "training_started" && <p className="text-emerald-400 text-sm mt-4">✅ Training started in background. Monitor the table below.</p>}
      </div>

      {/* Model Versions Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-zinc-800">
          <h2 className="text-xl font-semibold text-zinc-100">Model Registry</h2>
        </div>
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-8 text-center text-zinc-500">Loading...</div>
          ) : models && models.length > 0 ? (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-zinc-950 border-b border-zinc-800 text-sm uppercase text-zinc-400 font-medium tracking-wider">
                  <th className="p-4 pl-6">Algorithm</th>
                  <th className="p-4">Version</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">R² Score</th>
                  <th className="p-4">Training Time</th>
                  <th className="p-4">Created At</th>
                  <th className="p-4 pr-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {models.flatMap(model => 
                  model.versions.map(version => (
                    <tr key={version.id} className="hover:bg-zinc-800/30 transition-colors">
                      <td className="p-4 pl-6 text-zinc-300 font-medium">{model.name}</td>
                      <td className="p-4 text-zinc-400">{version.version_tag}</td>
                      <td className="p-4">
                        <StatusBadge status={version.status} />
                      </td>
                      <td className="p-4 text-zinc-300">
                        {version.r2_score ? (version.r2_score * 100).toFixed(2) + "%" : "-"}
                      </td>
                      <td className="p-4 text-zinc-400">
                        {version.training_time_seconds ? `${version.training_time_seconds.toFixed(1)}s` : "-"}
                      </td>
                      <td className="p-4 text-zinc-500 text-sm">
                        {new Date(version.created_at).toLocaleString()}
                      </td>
                      <td className="p-4 pr-6 text-right">
                        {version.status === "trained" && (
                          <button
                            onClick={() => activateMutation.mutate(version.id)}
                            disabled={activateMutation.isPending}
                            className="text-indigo-400 hover:text-indigo-300 text-sm font-medium disabled:opacity-50"
                          >
                            Activate
                          </button>
                        )}
                        {version.status === "active" && (
                          <span className="text-emerald-500 text-sm font-medium">Production</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center text-zinc-500">No models found.</div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    training: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    trained: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
    active: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.2)]",
    archived: "bg-zinc-800 text-zinc-500 border-zinc-700",
    failed: "bg-red-500/10 text-red-400 border-red-500/20",
  };
  
  return (
    <span className={`px-2.5 py-1 text-xs font-medium rounded-full border uppercase tracking-wider ${colors[status.toLowerCase()] || colors.archived}`}>
      {status}
    </span>
  );
}
