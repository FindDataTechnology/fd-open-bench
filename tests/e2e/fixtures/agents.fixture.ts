/**
 * Test agent fixtures
 */

export interface TestAgent {
  id: string;
  name: string;
  description: string;
  adapter_type: 'openai' | 'langchain' | 'custom';
  config: Record<string, any>;
  pricing_config: Record<string, any>;
}

export const testAgents = {
  openaiAgent: {
    id: 'agent-001',
    name: 'OpenAI Agent',
    description: 'Test OpenAI agent',
    adapter_type: 'openai' as const,
    config: {
      model: 'gpt-4o',
      temperature: 0.7,
      max_tokens: 1000,
    },
    pricing_config: {
      type: 'tokens',
      pricing: {
        'gpt-4o': {
          input_per_1k: 0.0025,
          output_per_1k: 0.01,
        },
      },
    },
  },
  langchainAgent: {
    id: 'agent-002',
    name: 'LangChain Agent',
    description: 'Test LangChain agent',
    adapter_type: 'langchain' as const,
    config: {
      model: 'gpt-3.5-turbo',
      chain_type: 'llm',
    },
    pricing_config: {
      type: 'per_minute',
      rate: 0.10,
    },
  },
  customAgent: {
    id: 'agent-003',
    name: 'Custom Agent',
    description: 'Test custom agent',
    adapter_type: 'custom' as const,
    config: {
      endpoint: 'http://localhost:8000/api/agent',
    },
    pricing_config: {
      type: 'per_hour',
      rate: 6.00,
    },
  },
};

/**
 * Create a test agent with custom values
 */
export function createAgent(overrides: Partial<TestAgent> = {}): TestAgent {
  return {
    id: `agent-${Date.now()}`,
    name: `Test Agent ${Date.now()}`,
    description: 'Test agent description',
    adapter_type: 'openai',
    config: {},
    pricing_config: {},
    ...overrides,
  };
}
