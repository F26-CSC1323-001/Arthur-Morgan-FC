const statBtn = document.getElementById('statBtn');

if (statBtn) {
    statBtn.addEventListener('click', () => {
        window.location.href = 'status.html'
    })
}

const homeBtn = document.getElementById('homeBtn');

if (homeBtn) {
    homeBtn.addEventListener('click', () => {
        window.location.href = 'home.html'
    })
}

const helpBtn = document.getElementById('helpBtn');

if (helpBtn) {
    helpBtn.addEventListener('click', () => {
        window.location.href = 'help.html'
    })
}

const abtBtn = document.getElementById('abtBtn');

if (abtBtn) {
    abtBtn.addEventListener('click', () => {
        window.location.href = 'about.html'
    })
}

const accountBtn = document.getElementById('accountBtn');

if (accountBtn) {
    accountBtn.addEventListener('click', () => {
        window.location.href = 'account.html'
    })
}

const settingsBtn = document.getElementById('settingsBtn');

if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
        window.location.href = 'settings.html'
    })
}

const logsBtn = document.getElementById('logsBtn');

if (logsBtn) {
    logsBtn.addEventListener('click', () => {
        window.location.href='display.html'
    })
}

const viewBtn = document.getElementById('viewBtn');

if (viewBtn) {
    viewBtn.addEventListener('click', () =>{
        window.location.href = 'logs.html'
    })
}

const backBtn = document.getElementById('backBtn');

if (backBtn) {
    backBtn.addEventListener('click', () => {
        window.history.back();
    })
}

const loginBtn = document.getElementById('loginBtn');

if(loginBtn) {
    loginBtn.addEventListener('click', () => {
        window.location.href = "login.html"
    })
}