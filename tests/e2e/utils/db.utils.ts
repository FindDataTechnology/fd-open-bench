/**
 * Database utilities for test data management
 */

import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';

const DATABASE_URL = process.env.E2E_DATABASE_URL || 'sqlite:///./fd_open_bench.db';

/**
 * Seed test data into database using Python scripts
 */
export async function seedTestData(): Promise<void> {
  const seedScriptPath = path.join(process.cwd(), 'scripts/seed_test_data.py');

  if (!fs.existsSync(seedScriptPath)) {
    console.log('Seed script not found, skipping database seeding...');
    return;
  }

  await executePythonScript(seedScriptPath);
}

/**
 * Clean up test data after test suites
 */
export async function cleanupTestData(): Promise<void> {
  const cleanupScriptPath = path.join(process.cwd(), 'scripts/cleanup_test_data.py');

  if (!fs.existsSync(cleanupScriptPath)) {
    console.log('Cleanup script not found, skipping cleanup...');
    return;
  }

  await executePythonScript(cleanupScriptPath);
}

/**
 * Execute Python script
 */
function executePythonScript(scriptPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    exec(`python3 "${scriptPath}"`, (error, stdout, stderr) => {
      if (error) {
        console.error(`Error executing script: ${stderr}`);
        reject(error);
        return;
      }

      console.log(stdout);
      resolve();
    });
  });
}

/**
 * Get current timestamp for unique identifiers
 */
export function getTimestamp(): string {
  return Date.now().toString();
}

/**
 * Generate random UUID
 */
export function generateUUID(): string {
  return crypto.randomUUID?.() || `test-${Date.now()}-${Math.random().toString(36).substring(7)}`;
}

/**
 * Sanitize test entity name
 */
export function sanitizeName(name: string): string {
  return `${name}-${getTimestamp()}`;
}

/**
 * Create test entity with unique suffix
 */
export function createTestEntity(
  baseName: string,
  suffix?: string
): string {
  return `${baseName}-${suffix || getTimestamp()}`;
}
