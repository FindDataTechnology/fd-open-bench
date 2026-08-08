/**
 * Test dataset fixtures
 */

export interface TestGolden {
  id: string;
  input: string;
  expected_output?: string;
  expected_tools?: string[];
  business_value?: number;
  metadata?: Record<string, any>;
}

export interface TestDataset {
  id: string;
  name: string;
  description: string;
  goldens: TestGolden[];
}

export const testDatasets = {
  flightBooking: {
    id: 'dataset-001',
    name: 'Flight Booking Tests',
    description: 'Test cases for flight booking agent',
    goldens: [
      {
        id: 'golden-001',
        input: 'Find cheapest flight from NYC to London next week',
        expected_output: 'Flight found for $450',
        expected_tools: ['search_flights'],
        business_value: 50.0,
      },
      {
        id: 'golden-002',
        input: 'Book round-trip flight NYC-London April 1-8',
        expected_output: 'Flight booked successfully',
        expected_tools: ['search_flights', 'book_flight'],
        business_value: 100.0,
      },
    ],
  },
  customerSupport: {
    id: 'dataset-002',
    name: 'Customer Support Tests',
    description: 'Test cases for customer support agent',
    goldens: [
      {
        id: 'golden-003',
        input: 'My order #12345 hasn\'t arrived yet',
        expected_output: 'Let me check your order status',
        business_value: 25.0,
      },
      {
        id: 'golden-004',
        input: 'I want to return item from order #12345',
        expected_output: 'Return initiated successfully',
        expected_tools: ['lookup_order', 'initiate_return'],
        business_value: 10.0,
      },
    ],
  },
};

/**
 * Create a test dataset with custom values
 */
export function createDataset(overrides: Partial<TestDataset> = {}): TestDataset {
  return {
    id: `dataset-${Date.now()}`,
    name: `Test Dataset ${Date.now()}`,
    description: 'Test dataset description',
    goldens: [],
    ...overrides,
  };
}

/**
 * Create a test golden with custom values
 */
export function createGolden(overrides: Partial<TestGolden> = {}): TestGolden {
  return {
    id: `golden-${Date.now()}`,
    input: 'Test input',
    expected_output: 'Test output',
    business_value: 10.0,
    ...overrides,
  };
}
