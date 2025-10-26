// Service Worker for Push Notifications
console.log('Service Worker Loaded...');

self.addEventListener('push', function(event) {
    console.log('Push Received:', event);

    let notificationData = {};
    
    try {
        if (event.data) {
            notificationData = event.data.json();
        }
    } catch (e) {
        notificationData = {
            title: 'Pharmacy App',
            body: event.data ? event.data.text() : 'You have a new notification',
            icon: '/static/authentication/icon.png',
            badge: '/static/authentication/badge.png'
        };
    }

    const title = notificationData.title || 'Pharmacy App';
    const options = {
        body: notificationData.body || 'You have a new notification',
        icon: notificationData.icon || '/static/authentication/icon.png',
        badge: notificationData.badge || '/static/authentication/badge.png',
        vibrate: [200, 100, 200],
        data: notificationData.data || {},
        actions: notificationData.actions || []
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    console.log('Notification clicked:', event);
    
    event.notification.close();

    // Handle notification click - open the app
    event.waitUntil(
        clients.openWindow(event.notification.data.url || '/')
    );
});

self.addEventListener('notificationclose', function(event) {
    console.log('Notification closed:', event);
});
