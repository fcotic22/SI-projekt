const registrationSamples = window.APP_CONFIG.registrationSamples;
const minChars = window.APP_CONFIG.minChars;

const usernameInput = document.getElementById("username");
const typingArea = document.getElementById("typingArea");
const statusBox = document.getElementById("statusBox");

const registerButton = document.getElementById("registerButton");
const loginButton = document.getElementById("loginButton");
const resetButton = document.getElementById("resetButton");
const saveSampleButton = document.getElementById("saveSampleButton");

let mode = null;
let recording = false;
let samples = [];
let events = [];
let pressedKeys = {};

function setStatus(message, type) {
    statusBox.textContent = message;
    statusBox.className = "status " + type;
}

function getUsername() {
    return usernameInput.value.trim();
}

function resetCurrentSample() {
    events = [];
    pressedKeys = {};
    typingArea.value = "";
    typingArea.focus();
}

function enableTyping() {
    typingArea.disabled = false;
    saveSampleButton.disabled = false;
    recording = true;
    resetCurrentSample();
}

function disableTyping() {
    typingArea.disabled = true;
    saveSampleButton.disabled = true;
    recording = false;
    pressedKeys = {};
}

function resetAll() {
    mode = null;
    samples = [];
    events = [];
    pressedKeys = {};
    typingArea.value = "";
    disableTyping();
    setStatus("Start registration or login.", "info");
}

function startRegistration() {
    if (!getUsername()) {
        setStatus("Enter username first.", "error");
        return;
    }

    mode = "register";
    samples = [];
    enableTyping();

    setStatus(
        `Registration started.
Type any free text with at least ${minChars} characters.
Then click "Save current sample".
Sample 1/${registrationSamples}.`,
        "info"
    );
}

function startLogin() {
    if (!getUsername()) {
        setStatus("Enter username first.", "error");
        return;
    }

    mode = "login";
    samples = [];
    enableTyping();

    setStatus(
        `Login started.
Type any free text with at least ${minChars} characters.
Then click "Save current sample".`,
        "info"
    );
}

function keyId(event) {
    return event.code || event.key;
}

function keyName(event) {
    if (event.key === " ") {
        return "Space";
    }

    return event.key;
}

function saveCurrentSample() {
    if (!recording || mode === null) {
        setStatus("Start registration or login first.", "error");
        return;
    }

    const text = typingArea.value;

    if (text.length < minChars) {
        setStatus(
            `Text is too short. Current: ${text.length}/${minChars} characters.`,
            "error"
        );
        return;
    }

    const sample = {
        typedText: text,
        events: events
    };

    if (mode === "register") {
        samples.push(sample);

        if (samples.length < registrationSamples) {
            const nextSample = samples.length + 1;
            resetCurrentSample();

            setStatus(
                `Sample saved.
Type a new free-text sample.
Sample ${nextSample}/${registrationSamples}.`,
                "info"
            );

            return;
        }

        sendRegistration();
        return;
    }

    if (mode === "login") {
        sendLogin(sample);
    }
}

async function postJSON(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });
    return response.json();
}

async function sendRegistration() {
    disableTyping();

    const data = await postJSON("/api/register", { username: getUsername(), samples });

    if (data.ok) {
        setStatus(`${data.message}\nFeature count: ${data.feature_count}`, "success");
    } else {
        setStatus(data.message, "error");
    }
}

async function sendLogin(sample) {
    disableTyping();

    const data = await postJSON("/api/login", { username: getUsername(), sample });

    if (!data.ok) {
        setStatus(data.message, "error");
        return;
    }

    const type = data.approved ? "success" : "error";
    setStatus(
        `${data.message}\nDistance: ${data.distance}\nThreshold: ${data.threshold}`,
        type
    );
}

typingArea.addEventListener("keydown", function (event) {
    if (!recording) {
        return;
    }

    const id = keyId(event);

    if (event.repeat) {
        return;
    }

    if (pressedKeys[id] === undefined) {
        pressedKeys[id] = {
            key: keyName(event),
            code: event.code,
            press: performance.now() / 1000
        };
    }
});

typingArea.addEventListener("keyup", function (event) {
    if (!recording) {
        return;
    }

    const id = keyId(event);

    if (pressedKeys[id] === undefined) {
        return;
    }

    const started = pressedKeys[id];

    events.push({
        key: started.key,
        code: started.code,
        press: started.press,
        release: performance.now() / 1000
    });

    delete pressedKeys[id];
});

registerButton.addEventListener("click", startRegistration);
loginButton.addEventListener("click", startLogin);
resetButton.addEventListener("click", resetAll);
saveSampleButton.addEventListener("click", saveCurrentSample);