/**
 * Test evaluation fixtures
 */

export interface TestEvaluation {
  id: string;
  agent_id: string;
  dataset_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  tasks_total: number;
  tasks_completed: number;
  tasks_failed: number;
  current_cost: number;
  results_summary?: Record<string, any>;
}

export const testEvaluations = {
  completedEvaluation: {
    id: 'eval-001',
    agent_id: 'agent-001',
    dataset_id: 'dataset-001',
    status: 'completed' as const,
    tasks_total: 10,
    tasks_completed: 10,
    tasks_failed: 0,
    current_cost: 5.50,
    results_summary: {
      avg_score: 0.85,
      success_rate: 100,
      total_cost: 5.50,
    },
  },
  runningEvaluation: {
    id: 'eval-002',
    agent_id: 'agent-002',
    dataset_id: 'dataset-002',
    status: 'running' as const,
    tasks_total: 20,
    tasks_completed: 10,
    tasks_failed: 0,
    current_cost: 2.75,
  },
  failedEvaluation: {
    id: 'eval-003',
    agent_id: 'agent-003',
    dataset_id: 'dataset-001',
    status: 'failed' as const,
    tasks_total: 10,
    tasks_completed: 5,
    tasks_failed: 5,
    current_cost: 3.00,
  },
};

/**
 * Create a test evaluation with custom values
 */
export function createEvaluation(overrides: Partial<TestEvaluation> = {}): TestEvaluation {
  return {
    id: `eval-${Date.now()}`,
    agent_id: 'agent-001',
    dataset_id: 'dataset-001',
    status: 'pending',
    tasks_total: 10,
    tasks_completed: 0,
    tasks_failed: 0,
    current_cost: 0,
    ...overrides,
  };
}
