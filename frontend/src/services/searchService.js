import api from './api';

const searchService = {
    /**
     * search
     * @param {string} query - The search query
     * @returns {Promise<Object>} - The search results
     */
    search: async (query, filters = {}) => {
        // New Endpoint: /api/search/?q=...
        const params = { q: query, ...filters };
        const response = await api.get(`/search/`, { params });
        return response.data;
    },

    /**
     * getSupplierDetails
     * @param {string} sellerName - Name of the seller
     * @param {string} query - The original query (context)
     * @returns {Promise<Object>} - The supplier details
     */
    getSupplierDetails: async (sellerName, query) => {
        // New Endpoint: /api/search/supplier-detail/
        const response = await api.get(`/search/supplier-detail/`, {
            params: { name: sellerName, query: query }
        });
        return response.data;
    }
};

export default searchService;
