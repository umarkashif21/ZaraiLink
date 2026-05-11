import api from './api';

const searchService = {
    search: async (query, filters = {}) => {
        const params = { q: query, ...filters };
        const response = await api.get(`/search/`, { params });
        return response.data;
    },

    getSupplierDetails: async (sellerName, query, scope, subcatId, variantName, intent) => {
        const params = { name: sellerName, query: query };
        if (scope)       params.scope        = scope;
        if (subcatId)    params.subcat_id    = subcatId;
        if (variantName) params.variant_name = variantName;
        if (intent)      params.intent       = intent;

        const response = await api.get(`/search/supplier-detail/`, { params });
        return response.data;
    },

    compareSuppliers: async (supplierNames, query, scope, subcatId, variantName, intent) => {
        const params = { suppliers: supplierNames.join(','), query };
        if (scope) params.scope = scope;
        if (subcatId) params.subcat_id = subcatId;
        if (variantName) params.variant_name = variantName;
        if (intent) params.intent = intent;

        const response = await api.get(`/search/compare/`, { params });
        return response.data;
    },

    getSupplierTransactions: async (sellerName, query, scope, subcatId, variantName, intent, page, pageSize, filters) => {
        const params = { name: sellerName, query: query, page, page_size: pageSize, ...filters };
        if (scope)       params.scope        = scope;
        if (subcatId)    params.subcat_id    = subcatId;
        if (variantName) params.variant_name = variantName;
        if (intent)      params.intent       = intent;

        const response = await api.get(`/search/supplier-transactions/`, { params });
        return response.data;
    }
};

export default searchService;
