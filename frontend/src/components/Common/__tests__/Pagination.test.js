
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';


const Pagination = ({ 
  currentPage, 
  totalPages, 
  onPageChange,
  showFirstLast = true
}) => {
  if (totalPages <= 1) return null;

  const getVisiblePages = () => {
    const pages = [];
    const start = Math.max(1, currentPage - 2);
    const end = Math.min(totalPages, currentPage + 2);
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };

  return (
    <div className="pagination" data-testid="pagination">
      {showFirstLast && currentPage > 1 && (
        <button 
          onClick={() => onPageChange(1)} 
          data-testid="first-page"
        >
          First
        </button>
      )}
      
      <button 
        onClick={() => onPageChange(currentPage - 1)} 
        disabled={currentPage === 1}
        data-testid="prev-page"
      >
        Previous
      </button>

      {getVisiblePages().map(page => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={page === currentPage ? 'active' : ''}
          data-testid={`page-${page}`}
        >
          {page}
        </button>
      ))}

      <button 
        onClick={() => onPageChange(currentPage + 1)} 
        disabled={currentPage === totalPages}
        data-testid="next-page"
      >
        Next
      </button>

      {showFirstLast && currentPage < totalPages && (
        <button 
          onClick={() => onPageChange(totalPages)} 
          data-testid="last-page"
        >
          Last
        </button>
      )}
    </div>
  );
};

describe('Pagination Component', () => {
  test('does not render when totalPages is 1', () => {
    render(
      <Pagination currentPage={1} totalPages={1} onPageChange={() => {}} />
    );
    
    expect(screen.queryByTestId('pagination')).not.toBeInTheDocument();
  });

  test('renders pagination when totalPages > 1', () => {
    render(
      <Pagination currentPage={1} totalPages={5} onPageChange={() => {}} />
    );
    
    expect(screen.getByTestId('pagination')).toBeInTheDocument();
  });

  test('disables Previous button on first page', () => {
    render(
      <Pagination currentPage={1} totalPages={5} onPageChange={() => {}} />
    );
    
    expect(screen.getByTestId('prev-page')).toBeDisabled();
  });

  test('disables Next button on last page', () => {
    render(
      <Pagination currentPage={5} totalPages={5} onPageChange={() => {}} />
    );
    
    expect(screen.getByTestId('next-page')).toBeDisabled();
  });

  test('calls onPageChange with correct page number', () => {
    const onPageChange = jest.fn();
    render(
      <Pagination currentPage={3} totalPages={10} onPageChange={onPageChange} />
    );
    
    fireEvent.click(screen.getByTestId('page-4'));
    expect(onPageChange).toHaveBeenCalledWith(4);
  });

  test('Next button increments page', () => {
    const onPageChange = jest.fn();
    render(
      <Pagination currentPage={3} totalPages={10} onPageChange={onPageChange} />
    );
    
    fireEvent.click(screen.getByTestId('next-page'));
    expect(onPageChange).toHaveBeenCalledWith(4);
  });

  test('Previous button decrements page', () => {
    const onPageChange = jest.fn();
    render(
      <Pagination currentPage={3} totalPages={10} onPageChange={onPageChange} />
    );
    
    fireEvent.click(screen.getByTestId('prev-page'));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  test('shows First and Last buttons', () => {
    render(
      <Pagination currentPage={5} totalPages={10} onPageChange={() => {}} />
    );
    
    expect(screen.getByTestId('first-page')).toBeInTheDocument();
    expect(screen.getByTestId('last-page')).toBeInTheDocument();
  });

  test('First button goes to page 1', () => {
    const onPageChange = jest.fn();
    render(
      <Pagination currentPage={5} totalPages={10} onPageChange={onPageChange} />
    );
    
    fireEvent.click(screen.getByTestId('first-page'));
    expect(onPageChange).toHaveBeenCalledWith(1);
  });
});
