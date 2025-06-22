// Service Worker for FleetFuel360 PWA
// Provides offline functionality and caching

const CACHE_NAME = 'fleetfuel360-v1.0.0';
const OFFLINE_CACHE = 'fleetfuel360-offline-v1';

// Files to cache for offline functionality
const CACHE_FILES = [
    '/',
    '/executive',
    '/static/css/styles.css',
    '/static/js/chart.js',
    '/static/favicon.ico',
    '/static/manifest.json',
    // External dependencies
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.js'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
    '/api/health',
    '/api/vehicles',
    '/api/statistics',
    '/api/analytics/executive-summary'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
    console.log('FleetFuel360 Service Worker: Installing');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching files');
                return Promise.allSettled(
                    CACHE_FILES.map(url => 
                        cache.add(url).catch(err => {
                            console.warn(`Failed to cache ${url}:`, err);
                        })
                    )
                );
            })
            .then(() => {
                console.log('Service Worker: Installation completed');
                self.skipWaiting();
            })
            .catch((error) => {
                console.error('Service Worker: Installation failed', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('FleetFuel360 Service Worker: Activating');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME && cacheName !== OFFLINE_CACHE) {
                            console.log('Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker: Activation completed');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Handle API requests
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
        return;
    }
    
    // Handle navigation requests
    if (request.mode === 'navigate') {
        event.respondWith(handleNavigationRequest(request));
        return;
    }
    
    // Handle other requests (static assets, etc.)
    event.respondWith(handleStaticRequest(request));
});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
    const url = new URL(request.url);
    
    try {
        // Try network first for fresh data
        const networkResponse = await fetch(request);
        
        // Cache successful API responses
        if (networkResponse.ok && shouldCacheApiResponse(url.pathname)) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.warn('Network request failed, trying cache:', error);
        
        // Fallback to cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            // Add offline indicator header
            const response = cachedResponse.clone();
            response.headers.set('X-Served-By', 'ServiceWorker-Cache');
            return response;
        }
        
        // Return offline fallback for API requests
        return createOfflineApiResponse(url.pathname);
    }
}

// Handle navigation requests with cache-first for shell, network-first for content
async function handleNavigationRequest(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        // Cache the response
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, networkResponse.clone());
        
        return networkResponse;
    } catch (error) {
        console.warn('Navigation request failed, serving from cache:', error);
        
        // Fallback to cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Fallback to offline page
        return caches.match('/offline.html') || createOfflineHtmlResponse();
    }
}

// Handle static requests with cache-first strategy
async function handleStaticRequest(request) {
    // Try cache first for static assets
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        // Fallback to network
        const networkResponse = await fetch(request);
        
        // Cache the response for future use
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.warn('Static request failed:', error);
        
        // Return placeholder for failed static requests
        if (request.destination === 'image') {
            return createPlaceholderImageResponse();
        }
        
        return new Response('Offline', { status: 503 });
    }
}

// Check if API response should be cached
function shouldCacheApiResponse(pathname) {
    return API_CACHE_PATTERNS.some(pattern => pathname.includes(pattern));
}

// Create offline API response
function createOfflineApiResponse(pathname) {
    const offlineData = {
        status: 'offline',
        message: 'You are currently offline. Showing cached data.',
        timestamp: new Date().toISOString(),
        data: getOfflineFallbackData(pathname)
    };
    
    return new Response(JSON.stringify(offlineData), {
        status: 200,
        headers: {
            'Content-Type': 'application/json',
            'X-Served-By': 'ServiceWorker-Offline'
        }
    });
}

// Get offline fallback data for different endpoints
function getOfflineFallbackData(pathname) {
    if (pathname.includes('executive-summary')) {
        return {
            key_metrics: {
                total_vehicles: 'N/A',
                total_fuel_cost: 'N/A',
                average_efficiency: 'N/A',
                anomaly_rate: 'N/A'
            },
            alert_summary: {
                critical: 0,
                high: 0,
                medium: 0,
                low: 0
            }
        };
    }
    
    if (pathname.includes('vehicles')) {
        return [];
    }
    
    if (pathname.includes('statistics')) {
        return {
            total_vehicles: 'Offline',
            total_logs: 'Offline',
            average_efficiency: 'Offline'
        };
    }
    
    return {};
}

// Create offline HTML response
function createOfflineHtmlResponse() {
    const offlineHtml = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>FleetFuel360 - Offline</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background-color: #ecf0f1;
                }
                .offline-container {
                    max-width: 500px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 15px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }
                .offline-icon {
                    font-size: 4rem;
                    color: #e74c3c;
                    margin-bottom: 20px;
                }
                .retry-btn {
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    margin-top: 20px;
                }
                .retry-btn:hover {
                    background: #2980b9;
                }
            </style>
        </head>
        <body>
            <div class="offline-container">
                <div class="offline-icon">📡</div>
                <h1>You're Offline</h1>
                <p>FleetFuel360 requires an internet connection to display live data.</p>
                <p>Please check your connection and try again.</p>
                <button class="retry-btn" onclick="window.location.reload()">
                    Retry Connection
                </button>
            </div>
        </body>
        </html>
    `;
    
    return new Response(offlineHtml, {
        status: 200,
        headers: { 'Content-Type': 'text/html' }
    });
}

// Create placeholder image response
function createPlaceholderImageResponse() {
    // Simple 1x1 transparent pixel
    const transparentPixel = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
    
    return fetch(transparentPixel);
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    console.log('Background sync triggered:', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(syncOfflineActions());
    }
});

// Sync offline actions when back online
async function syncOfflineActions() {
    console.log('Syncing offline actions...');
    
    try {
        // Get offline actions from IndexedDB or localStorage
        const offlineActions = await getOfflineActions();
        
        for (const action of offlineActions) {
            try {
                await fetch(action.url, action.options);
                // Remove successful action
                await removeOfflineAction(action.id);
            } catch (error) {
                console.warn('Failed to sync action:', action, error);
            }
        }
        
        console.log('Offline actions synced successfully');
    } catch (error) {
        console.error('Error syncing offline actions:', error);
    }
}

// Placeholder functions for offline action management
async function getOfflineActions() {
    // Implementation would use IndexedDB
    return [];
}

async function removeOfflineAction(actionId) {
    // Implementation would remove from IndexedDB
    console.log('Removing offline action:', actionId);
}

// Push notification handling
self.addEventListener('push', (event) => {
    console.log('Push notification received:', event);
    
    const options = {
        body: event.data ? event.data.text() : 'New FleetFuel360 notification',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            timestamp: Date.now()
        },
        actions: [
            {
                action: 'view',
                title: 'View Dashboard',
                icon: '/static/icons/view-action.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/icons/dismiss-action.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('FleetFuel360', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/')
        );
    } else if (event.action === 'dismiss') {
        // Just close the notification
        return;
    } else {
        // Default action - open main dashboard
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Message handling from main thread
self.addEventListener('message', (event) => {
    console.log('Service Worker received message:', event.data);
    
    if (event.data.action === 'skipWaiting') {
        self.skipWaiting();
    }
    
    if (event.data.action === 'getCacheStatus') {
        event.ports[0].postMessage({
            cacheStatus: 'active',
            cacheSize: CACHE_FILES.length
        });
    }
});

console.log('FleetFuel360 Service Worker loaded successfully');
