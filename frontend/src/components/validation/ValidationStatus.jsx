import React from 'react';
import { CheckCircleIcon, ExclamationCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/solid';

const ValidationStatus = ({ validationResult, isValidating = false }) => {
  if (isValidating) {
    return (
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
        <div className="flex items-center">
          <ClockIcon className="h-5 w-5 text-blue-500 animate-spin mr-2" />
          <span className="text-blue-700 dark:text-blue-300 font-medium">
            Validating content...
          </span>
        </div>
      </div>
    );
  }

  if (!validationResult) {
    return null;
  }

  const getStatusIcon = (success) => {
    if (success) {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
    }
    return <XCircleIcon className="h-5 w-5 text-red-500" />;
  };

  const getQualityTierColor = (tier) => {
    switch (tier) {
      case 'premium':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300';
      case 'standard':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
      case 'basic':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300';
      case 'rejected':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-green-600 dark:text-green-400';
    if (score >= 6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
          {getStatusIcon(validationResult.overall_success)}
          <span className="ml-2">Validation Results</span>
        </h3>
        <div className="flex items-center space-x-3">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getQualityTierColor(validationResult.quality_tier)}`}>
            {validationResult.quality_tier?.toUpperCase() || 'UNKNOWN'}
          </span>
          <div className="text-right">
            <div className="text-sm text-gray-500 dark:text-gray-400">Quality Score</div>
            <div className={`text-xl font-bold ${getScoreColor(validationResult.overall_quality_score)}`}>
              {validationResult.overall_quality_score?.toFixed(1) || 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Phase Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        {Object.entries(validationResult.phase_results || {}).map(([phase, result]) => {
          if (!result) return null;

          const phaseNames = {
            'html_js': 'HTML/JS',
            'scientific': 'Scientific',
            'realism': 'Realism',
            'runtime': 'Runtime'
          };

          return (
            <div key={phase} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {phaseNames[phase] || phase}
                </span>
                {getStatusIcon(result.success)}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Score: <span className={getScoreColor(result.score)}>{result.score?.toFixed(1) || 'N/A'}</span>
              </div>
              {result.issues_count > 0 && (
                <div className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                  {result.issues_count} issue{result.issues_count !== 1 ? 's' : ''}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Critical Issues */}
      {validationResult.critical_issues && validationResult.critical_issues.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-4">
          <div className="flex items-center mb-2">
            <ExclamationCircleIcon className="h-5 w-5 text-red-500 mr-2" />
            <span className="font-medium text-red-700 dark:text-red-300">
              Critical Issues ({validationResult.critical_issues.length})
            </span>
          </div>
          <ul className="list-disc list-inside text-sm text-red-600 dark:text-red-400 space-y-1">
            {validationResult.critical_issues.slice(0, 3).map((issue, index) => (
              <li key={index}>{issue.message}</li>
            ))}
            {validationResult.critical_issues.length > 3 && (
              <li className="text-red-500 dark:text-red-400">
                ...and {validationResult.critical_issues.length - 3} more
              </li>
            )}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {validationResult.recommendations && validationResult.recommendations.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
          <div className="flex items-center mb-2">
            <CheckCircleIcon className="h-5 w-5 text-blue-500 mr-2" />
            <span className="font-medium text-blue-700 dark:text-blue-300">
              Recommendations ({validationResult.recommendations.length})
            </span>
          </div>
          <ul className="list-disc list-inside text-sm text-blue-600 dark:text-blue-400 space-y-1">
            {validationResult.recommendations.slice(0, 2).map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
            {validationResult.recommendations.length > 2 && (
              <li className="text-blue-500 dark:text-blue-400">
                ...and {validationResult.recommendations.length - 2} more
              </li>
            )}
          </ul>
        </div>
      )}

      {/* Validation Timing */}
      {validationResult.validation_time && (
        <div className="mt-3 text-xs text-gray-500 dark:text-gray-400 text-right">
          Validated in {validationResult.validation_time.toFixed(2)}s
        </div>
      )}
    </div>
  );
};

export default ValidationStatus;
