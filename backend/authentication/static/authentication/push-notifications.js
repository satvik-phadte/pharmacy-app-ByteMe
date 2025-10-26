// Push Notification Helper
const pushNotification = {
    publicKey: null,
    
    init: function(publicKey) {
        this.publicKey = publicKey;
        this.registerServiceWorker();
    },

    registerServiceWorker: function() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/authentication/service-worker.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                    this.checkSubscription(registration);
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        } else {
            console.warn('Service Workers are not supported in this browser');
        }
    },

    checkSubscription: function(registration) {
        registration.pushManager.getSubscription()
            .then(subscription => {
                if (subscription) {
                    console.log('Already subscribed:', subscription);
                    this.updateUI(true);
                } else {
                    console.log('Not subscribed yet');
                    this.updateUI(false);
                }
            });
    },

    urlBase64ToUint8Array: function(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    },

    subscribe: function() {
        if (!this.publicKey) {
            console.error('Public key not set');
            return Promise.reject('Public key not set');
        }

        return navigator.serviceWorker.ready
            .then(registration => {
                const convertedVapidKey = this.urlBase64ToUint8Array(this.publicKey);
                
                return registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: convertedVapidKey
                });
            })
            .then(subscription => {
                console.log('Subscribed:', subscription);
                return this.sendSubscriptionToServer(subscription);
            })
            .then(() => {
                this.updateUI(true);
                return true;
            })
            .catch(error => {
                console.error('Subscription failed:', error);
                throw error;
            });
    },

    unsubscribe: function() {
        return navigator.serviceWorker.ready
            .then(registration => {
                return registration.pushManager.getSubscription();
            })
            .then(subscription => {
                if (subscription) {
                    return subscription.unsubscribe()
                        .then(() => {
                            return this.deleteSubscriptionFromServer(subscription);
                        });
                }
            })
            .then(() => {
                this.updateUI(false);
                console.log('Unsubscribed successfully');
                return true;
            })
            .catch(error => {
                console.error('Unsubscribe failed:', error);
                throw error;
            });
    },

    sendSubscriptionToServer: function(subscription) {
        const subscriptionJson = subscription.toJSON();
        
        return fetch('/webpush/save_information', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({
                subscription: subscriptionJson,
                status_type: 'subscribe'
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to save subscription');
            }
            return response.json();
        });
    },

    deleteSubscriptionFromServer: function(subscription) {
        const subscriptionJson = subscription.toJSON();
        
        return fetch('/webpush/save_information', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({
                subscription: subscriptionJson,
                status_type: 'unsubscribe'
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to delete subscription');
            }
            return response.json();
        });
    },

    getCookie: function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    updateUI: function(isSubscribed) {
        const enableBtn = document.getElementById('enable-notifications-btn');
        const disableBtn = document.getElementById('disable-notifications-btn');
        const status = document.getElementById('notification-status');

        if (enableBtn && disableBtn && status) {
            if (isSubscribed) {
                enableBtn.style.display = 'none';
                disableBtn.style.display = 'inline-block';
                status.textContent = '✓ Notifications Enabled';
                status.className = 'notification-status enabled';
            } else {
                enableBtn.style.display = 'inline-block';
                disableBtn.style.display = 'none';
                status.textContent = '✗ Notifications Disabled';
                status.className = 'notification-status disabled';
            }
        }
    },

    requestPermission: function() {
        return new Promise((resolve, reject) => {
            const permissionResult = Notification.requestPermission(result => {
                resolve(result);
            });

            if (permissionResult) {
                permissionResult.then(resolve, reject);
            }
        })
        .then(permission => {
            if (permission === 'granted') {
                console.log('Notification permission granted');
                return this.subscribe();
            } else {
                console.log('Notification permission denied');
                throw new Error('Permission denied');
            }
        });
    }
};

// Export for use in templates
window.pushNotification = pushNotification;
