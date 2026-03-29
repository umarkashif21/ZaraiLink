import axios from 'axios';

const api = axios.create({
    baseURL: `${process.env.REACT_APP_API_BASE_URL}/api`, // Adjust if needed
    withCredentials: true, // Important for session cookies
    headers: {
        'Content-Type': 'application/json',
    },
});

export default api;
