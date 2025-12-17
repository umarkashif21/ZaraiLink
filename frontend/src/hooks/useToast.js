import toast from 'react-hot-toast';


const useToast = () => {
  const showSuccess = (message, options = {}) => {
    return toast.success(message, {
      duration: 4000,
      ...options,
    });
  };

  const showError = (message, options = {}) => {
    return toast.error(message, {
      duration: 5000,
      ...options,
    });
  };

  const showInfo = (message, options = {}) => {
    return toast(message, {
      icon: 'ℹ️',
      duration: 4000,
      ...options,
    });
  };

  const showWarning = (message, options = {}) => {
    return toast(message, {
      icon: '⚠️',
      duration: 5000,
      style: {
        borderLeft: '4px solid #f59e0b',
      },
      ...options,
    });
  };

  const showLoading = (message = 'Loading...', options = {}) => {
    return toast.loading(message, {
      ...options,
    });
  };

  const dismissToast = (toastId) => {
    toast.dismiss(toastId);
  };

  const dismissAll = () => {
    toast.dismiss();
  };

  
  const showPromise = (promise, messages, options = {}) => {
    return toast.promise(promise, {
      loading: messages.loading || 'Loading...',
      success: messages.success || 'Success!',
      error: messages.error || 'Something went wrong',
    }, {
      ...options,
    });
  };

  
  const showWithAction = (message, actionLabel, onAction, options = {}) => {
    return toast(
      (t) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span>{message}</span>
          <button
            onClick={() => {
              onAction();
              toast.dismiss(t.id);
            }}
            style={{
              background: 'var(--color-primary)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '0.85rem',
              whiteSpace: 'nowrap',
            }}
          >
            {actionLabel}
          </button>
        </div>
      ),
      {
        duration: 6000,
        ...options,
      }
    );
  };

  
  const showConfirmation = (message, onConfirm, onCancel = () => {}) => {
    return toast(
      (t) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <span>{message}</span>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <button
              onClick={() => {
                onCancel();
                toast.dismiss(t.id);
              }}
              style={{
                background: 'var(--bg-tertiary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-primary)',
                borderRadius: '6px',
                padding: '6px 12px',
                cursor: 'pointer',
                fontWeight: 500,
                fontSize: '0.85rem',
              }}
            >
              Cancel
            </button>
            <button
              onClick={() => {
                onConfirm();
                toast.dismiss(t.id);
              }}
              style={{
                background: 'var(--color-primary)',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                padding: '6px 12px',
                cursor: 'pointer',
                fontWeight: 500,
                fontSize: '0.85rem',
              }}
            >
              Confirm
            </button>
          </div>
        </div>
      ),
      {
        duration: Infinity,
      }
    );
  };

  return {
    showSuccess,
    showError,
    showInfo,
    showWarning,
    showLoading,
    showPromise,
    showWithAction,
    showConfirmation,
    dismissToast,
    dismissAll,
    
    toast,
  };
};

export default useToast;
