import React from 'react';
import { Shield, AlertTriangle, AlertOctagon, CheckCircle2 } from 'lucide-react';
import { RiskLevel } from '../types';

interface RiskBadgeProps {
  level: RiskLevel;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level }) => {
  switch (level.toLowerCase()) {
    case 'critical':
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-red-950/80 text-red-400 border border-red-800/60">
          <AlertOctagon className="w-3.5 h-3.5 mr-1 text-red-400 animate-pulse" />
          CRITICAL RISK
        </span>
      );
    case 'high':
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-orange-950/80 text-orange-400 border border-orange-800/60">
          <AlertTriangle className="w-3.5 h-3.5 mr-1 text-orange-400" />
          HIGH RISK
        </span>
      );
    case 'medium':
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-800/60">
          <Shield className="w-3.5 h-3.5 mr-1 text-amber-400" />
          MEDIUM RISK
        </span>
      );
    case 'low':
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
          <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-400" />
          LOW RISK
        </span>
      );
  }
};
