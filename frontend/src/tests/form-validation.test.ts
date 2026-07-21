import { describe, it, expect } from 'vitest';
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

const vehiclePredictionSchema = z.object({
  make: z.string().min(1),
  model: z.string().min(1),
  year: z.number().min(1990).max(new Date().getFullYear()),
  mileage: z.number().min(0),
});

describe('Form Validation Schemas', () => {
  it('should validate a correct login form', () => {
    const result = loginSchema.safeParse({ email: 'test@example.com', password: 'password123' });
    expect(result.success).toBe(true);
  });

  it('should reject invalid email', () => {
    const result = loginSchema.safeParse({ email: 'invalid-email', password: 'password123' });
    expect(result.success).toBe(false);
  });

  it('should validate valid vehicle details', () => {
    const result = vehiclePredictionSchema.safeParse({
      make: 'Honda',
      model: 'Civic',
      year: 2018,
      mileage: 45000,
    });
    expect(result.success).toBe(true);
  });

  it('should reject invalid year for vehicle', () => {
    const result = vehiclePredictionSchema.safeParse({
      make: 'Honda',
      model: 'Civic',
      year: 1800,
      mileage: 45000,
    });
    expect(result.success).toBe(false);
  });
});
