import React, { useCallback } from 'react';
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { ShieldAlert, Building2, Banknote, Briefcase } from 'lucide-react';

const GlassNode = ({ data }) => {
  const getBorderColor = () => {
    switch(data.entityType) {
      case 'promoter': return 'border-trust-blue shadow-[0_0_10px_rgba(21,101,192,0.3)]';
      case 'lender_safe': return 'border-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.3)]';
      case 'lender_risky': return 'border-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]';
      case 'shell': return 'border-orange-400 shadow-[0_0_10px_rgba(251,146,60,0.3)]';
      case 'subsidiary': return 'border-electric-cyan shadow-[0_0_10px_rgba(0,255,255,0.3)]';
      default: return 'border-navy-600';
    }
  };

  const getIcon = () => {
    switch(data.entityType) {
      case 'promoter': return <Briefcase className="w-4 h-4 text-trust-blue" />;
      case 'lender_safe': return <Banknote className="w-4 h-4 text-emerald-400" />;
      case 'lender_risky': return <ShieldAlert className="w-4 h-4 text-red-500" />;
      case 'shell': return <Building2 className="w-4 h-4 text-orange-400" />;
      case 'subsidiary': return <Building2 className="w-4 h-4 text-electric-cyan" />;
      default: return null;
    }
  };

  return (
    <div className={`glass-panel p-3 border-2 rounded-lg min-w-[160px] ${getBorderColor()} bg-navy-900/90 backdrop-blur-md relative`}>
      <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-navy-400 border-none" />
      <div className="flex items-center gap-2 mb-1 border-b border-navy-700/50 pb-2">
        {getIcon()}
        <span className="text-xs font-bold text-white tracking-wider">{data.label}</span>
      </div>
      {data.description && (
         <p className="text-[10px] text-trust-silver mt-2 leading-tight">{data.description}</p>
      )}
      <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-navy-400 border-none" />
    </div>
  );
};

const nodeTypes = {
  glass: GlassNode,
};

export default function ShadowNetworkGraph({ initialNodes = [], initialEdges = [] }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ 
        ...params, 
        animated: true, 
        style: { stroke: '#0ea5e9', strokeWidth: 2 } 
    }, eds)),
    [setEdges]
  );

  return (
    <div style={{ width: '100%', height: '450px' }} className="rounded-xl overflow-hidden border border-navy-700 relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        className="bg-navy-950"
      >
        <Background color="#1e293b" gap={16} size={1} />
      </ReactFlow>
    </div>
  );
}
