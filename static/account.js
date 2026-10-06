document.addEventListener('DOMContentLoaded', () => {
    const authPanel = document.getElementById('auth-panel');
    const profilePanel = document.getElementById('profile-panel');
    const accountTitle = document.getElementById('account-title');
    const message = document.getElementById('account-message');
    const authForm = document.getElementById('auth-form');
    const profileForm = document.getElementById('profile-form');
    const loginTab = document.getElementById('tab-login');
    const registerTab = document.getElementById('tab-register');
    const nameField = document.getElementById('name-field');
    const stateField = document.getElementById('state-field');
    const cropsField = document.getElementById('crops-field');
    const nameInput = document.getElementById('auth-name');
    const stateInput = document.getElementById('auth-state');
    const cropsInput = document.getElementById('auth-crops');
    const passwordInput = document.getElementById('auth-password');
    const passwordHint = document.getElementById('password-hint');
    const submitButton = document.getElementById('auth-submit');
    const csrfCookieName = 'agro_csrf=';
    let mode = 'login';

    function showMessage(text, kind = 'error') {
        message.textContent = text;
        message.className = `account-message ${kind}`;
    }

    function clearMessage() {
        message.textContent = '';
        message.className = 'account-message hidden';
    }

    function csrfToken() {
        const cookie = document.cookie.split('; ').find((part) => part.startsWith(csrfCookieName));
        return cookie ? decodeURIComponent(cookie.slice(csrfCookieName.length)) : '';
    }

    async function requestJson(url, options = {}) {
        const headers = new Headers(options.headers || {});
        if (options.body) headers.set('Content-Type', 'application/json');
        const token = csrfToken();
        if (token) headers.set('X-CSRF-Token', token);
        const response = await fetch(url, {
            ...options,
            headers,
            credentials: 'same-origin'
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const detail = Array.isArray(data.detail)
                ? data.detail.map((item) => item.msg).join('. ')
                : data.detail;
            throw new Error(detail || 'The request could not be completed.');
        }
        return data;
    }

    function setMode(nextMode) {
        mode = nextMode;
        const registering = mode === 'register';
        nameField.classList.toggle('hidden', !registering);
        stateField.classList.toggle('hidden', !registering);
        cropsField.classList.toggle('hidden', !registering);
        nameInput.required = registering;
        stateInput.required = registering;
        cropsInput.required = registering;
        passwordInput.minLength = registering ? 12 : 1;
        passwordInput.autocomplete = registering ? 'new-password' : 'current-password';
        passwordHint.textContent = registering ? 'At least 12 characters' : '';
        submitButton.textContent = registering ? 'Create account' : 'Sign in';
        loginTab.classList.toggle('active', !registering);
        registerTab.classList.toggle('active', registering);
        loginTab.setAttribute('aria-selected', String(!registering));
        registerTab.setAttribute('aria-selected', String(registering));
        clearMessage();
    }

    function splitCrops(value) {
        return value.split(',').map((crop) => crop.trim()).filter(Boolean);
    }

    function showProfile(user) {
        authPanel.classList.add('hidden');
        profilePanel.classList.remove('hidden');
        accountTitle.textContent = 'Your farmer profile';
        document.getElementById('profile-email').textContent = user.email;
        document.getElementById('profile-name').value = user.name;
        document.getElementById('profile-state').value = user.state;
        document.getElementById('profile-crops').value = user.crops.join(', ');
        clearMessage();
    }

    loginTab.addEventListener('click', () => setMode('login'));
    registerTab.addEventListener('click', () => setMode('register'));

    authForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearMessage();
        submitButton.disabled = true;
        try {
            const payload = {
                email: document.getElementById('auth-email').value,
                password: passwordInput.value
            };
            if (mode === 'register') {
                Object.assign(payload, {
                    name: nameInput.value,
                    state: stateInput.value,
                    crops: splitCrops(cropsInput.value)
                });
            }
            const data = await requestJson(`/auth/${mode === 'register' ? 'register' : 'login'}`, {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            authForm.reset();
            showProfile(data.user);
            showMessage('Your account is ready.', 'success');
        } catch (error) {
            showMessage(error.message);
        } finally {
            submitButton.disabled = false;
        }
    });

    profileForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearMessage();
        const saveButton = profileForm.querySelector('button[type="submit"]');
        saveButton.disabled = true;
        try {
            const data = await requestJson('/auth/me', {
                method: 'PATCH',
                body: JSON.stringify({
                    name: document.getElementById('profile-name').value,
                    state: document.getElementById('profile-state').value,
                    crops: splitCrops(document.getElementById('profile-crops').value)
                })
            });
            showProfile(data.user);
            showMessage('Your profile has been saved.', 'success');
        } catch (error) {
            showMessage(error.message);
        } finally {
            saveButton.disabled = false;
        }
    });

    document.getElementById('logout-button').addEventListener('click', async (event) => {
        const button = event.currentTarget;
        button.disabled = true;
        try {
            await requestJson('/auth/logout', { method: 'POST' });
            profilePanel.classList.add('hidden');
            authPanel.classList.remove('hidden');
            accountTitle.textContent = 'Your farmer account';
            authForm.reset();
            setMode('login');
            showMessage('You have signed out.', 'success');
        } catch (error) {
            showMessage(error.message);
        } finally {
            button.disabled = false;
        }
    });

    async function initialize() {
        try {
            const status = await requestJson('/auth/status');
            if (!status.configured) {
                showMessage('Account storage is not configured yet. Set MONGODB_URI on the server to enable accounts.');
                return;
            }
            try {
                const data = await requestJson('/auth/me');
                showProfile(data.user);
            } catch (error) {
                if (error.message !== 'Please sign in') showMessage(error.message);
            }
        } catch (error) {
            showMessage(error.message);
        }
    }

    initialize();
});
