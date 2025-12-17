
import React, { useState } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';


const ThemeContext = React.createContext();

const ThemeProvider = ({ children, initialDark = false }) => {
  const [isDarkMode, setIsDarkMode] = useState(initialDark);

  const toggleTheme = () => {
    setIsDarkMode(prev => !prev);
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

const useTheme = () => React.useContext(ThemeContext);


const TestComponent = () => {
  const { isDarkMode, toggleTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme-status">{isDarkMode ? 'Dark' : 'Light'}</span>
      <button data-testid="toggle-btn" onClick={toggleTheme}>Toggle</button>
    </div>
  );
};

describe('ThemeContext', () => {
  test('defaults to light mode', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );
    
    expect(screen.getByTestId('theme-status')).toHaveTextContent('Light');
  });

  test('can initialize with dark mode', () => {
    render(
      <ThemeProvider initialDark={true}>
        <TestComponent />
      </ThemeProvider>
    );
    
    expect(screen.getByTestId('theme-status')).toHaveTextContent('Dark');
  });

  test('toggleTheme switches from light to dark', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );
    
    expect(screen.getByTestId('theme-status')).toHaveTextContent('Light');
    
    fireEvent.click(screen.getByTestId('toggle-btn'));
    
    expect(screen.getByTestId('theme-status')).toHaveTextContent('Dark');
  });

  test('toggleTheme switches from dark to light', () => {
    render(
      <ThemeProvider initialDark={true}>
        <TestComponent />
      </ThemeProvider>
    );
    
    expect(screen.getByTestId('theme-status')).toHaveTextContent('Dark');
    
    fireEvent.click(screen.getByTestId('toggle-btn'));
    
    expect(screen.getByTestId('theme-status')).toHaveTextContent('Light');
  });

  test('toggleTheme can be called multiple times', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );
    
    
    fireEvent.click(screen.getByTestId('toggle-btn'));
    expect(screen.getByTestId('theme-status')).toHaveTextContent('Dark');
    
    fireEvent.click(screen.getByTestId('toggle-btn'));
    expect(screen.getByTestId('theme-status')).toHaveTextContent('Light');
  });
});
