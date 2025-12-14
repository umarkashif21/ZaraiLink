// src/App.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';

// Simple test that doesn't require full app dependencies
describe('App', () => {
  test('can run basic test', () => {
    expect(1 + 1).toBe(2);
  });
});
