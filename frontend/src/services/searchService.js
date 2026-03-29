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
     * @param {string} scope - The original scope
     * @param {string} subcatId - Explicit DB subcategory id constraint
     * @param {string} variantName - Explicit product variant name constraint
     * @returns {Promise<Object>} - The supplier details
     */
    getSupplierDetails: async (sellerName, query, scope, subcatId, variantName) => {
        // New Endpoint: /api/search/supplier-detail/
        const params = { name: sellerName, query: query };
        if (scope) {
            params.scope = scope;
        }
        if (subcatId) params.subcat_id = subcatId;
        if (variantName) params.variant_name = variantName;

        const response = await api.get(`/search/supplier-detail/`, {
            params: params
        });
        return response.data;
    }
};

export default searchService;
