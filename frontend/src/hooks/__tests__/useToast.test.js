
import { renderHook, act } from '@testing-library/react';


jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
    dismiss: jest.fn(),
  },
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
    dismiss: jest.fn(),
  },
}));

import toast from 'react-hot-toast';


const useToast = () => {
  const showSuccess = (message, options = {}) => {
    return toast.success(message, { duration: 4000, ...options });
  };

  const showError = (message, options = {}) => {
    return toast.error(message, { duration: 5000, ...options });
  };

  const showLoading = (message = 'Loading...') => {
    return toast.loading(message);
  };

  const dismissToast = (id) => {
    toast.dismiss(id);
  };

  const dismissAll = () => {
    toast.dismiss();
  };

  return { showSuccess, showError, showLoading, dismissToast, dismissAll };
};

describe('useToast Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('showSuccess calls toast.success with message', () => {
    const { result } = renderHook(() => useToast());
    
    act(() => {
      result.current.showSuccess('Operation successful!');
    });

    expect(toast.success).toHaveBeenCalledWith(
      'Operation successful!',
      expect.objectContaining({ duration: 4000 })
    );
  });

  test('showError calls toast.error with message', () => {
    const { result } = renderHook(() => useToast());
    
    act(() => {
      result.current.showError('Something went wrong!');
    });

    expect(toast.error).toHaveBeenCalledWith(
      'Something went wrong!',
      expect.objectContaining({ duration: 5000 })
    );
  });

  test('showLoading calls toast.loading', () => {
    const { result } = renderHook(() => useToast());
    
    act(() => {
      result.current.showLoading('Please wait...');
    });

    expect(toast.loading).toHaveBeenCalledWith('Please wait...');
  });

  test('dismissAll calls toast.dismiss without id', () => {
    const { result } = renderHook(() => useToast());
    
    act(() => {
      result.current.dismissAll();
    });

    expect(toast.dismiss).toHaveBeenCalledWith();
  });
});
