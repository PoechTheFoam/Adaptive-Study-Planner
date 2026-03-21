const PROFILE_KEY = "axis-mentor-profile-id";

const state = {
    meta: null,
    profileSnapshot: null,
    activeTopic: null,
    session: null,
    answers: {},
    currentQuestionIndex: 0,
    questionStartedAt: 0,
    error: "",
};

document.addEventListener("DOMContentLoaded", () => {
    initialize().catch((error) => {
        console.error(error);
        renderMessage("Something went wrong while loading the workspace.");
    });
});

async function initialize() {
    state.meta = await api("/api/meta");
    renderProviderPill();

    const profileId = localStorage.getItem(PROFILE_KEY);
    if (profileId) {
        try {
            state.profileSnapshot = await api(`/api/profile/${profileId}`);
            state.activeTopic = getPreferredTopic();
            renderDashboard();
            return;
        } catch (error) {
            localStorage.removeItem(PROFILE_KEY);
        }
    }

    renderOnboarding();
}

function renderProviderPill() {
    const pill = document.getElementById("provider-pill");
    if (!state.meta || !pill) {
        return;
    }

    if (state.meta.ai.geminiEnabled) {
        pill.textContent = `Gemini live Â· ${state.meta.ai.geminiModel}`;
    } else {
        pill.textContent = "Local engine fallback";
    }
}

function renderMessage(message) {
    renderShell(`
        <section class="panel loading-state">
            <p>${escapeHtml(message)}</p>
        </section>
    `);
}

function renderOnboarding() {
    const topicOptions = state.meta.topics
        .map((topic) => `<option value="${escapeHtml(topic.id)}">${escapeHtml(topic.label)}</option>`)
        .join("");
    const levelOptions = state.meta.educationLevels
        .map((level) => `<option value="${escapeHtml(level)}">${escapeHtml(level)}</option>`)
        .join("");

    renderShell(`
        <section class="hero">
            <div class="hero-copy">
                <h2>Register once, then let the tutor adapt every session.</h2>
                <p>
                    Pick a math track and education level, then the system will generate a quiz,
                    score it with your weighted formula, explain every question, and save the learner profile
                    so the next session starts smarter.
                </p>
            </div>
            <div class="hero-aside">
                <div class="mini-note">
                    <strong>Adaptive loop</strong>
                    Questions, weighted scoring, difficulty updates, and saved progress all stay in one web flow.
                </div>
                <div class="mini-note">
                    <strong>Teacher-style feedback</strong>
                    Every session returns explanations, risk flags, consistency signals, and a next-step decision.
                </div>
            </div>
        </section>
        <section class="layout-grid">
            <section class="panel">
                <h3>Create learner profile</h3>
                <form id="register-form" class="form-grid">
                    <div class="input-row">
                        <label for="name">Student name</label>
                        <input id="name" name="name" placeholder="Ava, Minh, Jordan..." required>
                    </div>
                    <div class="input-row">
                        <label for="topic">Math focus</label>
                        <select id="topic" name="topic">${topicOptions}</select>
                    </div>
                    <div class="input-row">
                        <label for="educationLevel">Education level</label>
                        <select id="educationLevel" name="educationLevel">${levelOptions}</select>
                    </div>
                    <div class="button-row">
                        <button class="button" type="submit">Create and start assessment</button>
                    </div>
                </form>
                ${state.error ? `<div class="error-box">${escapeHtml(state.error)}</div>` : ""}
            </section>
            <aside class="panel">
                <h3>What gets tracked</h3>
                <div class="badge-row">
                    <div class="badge">
                        <span>Weighted score</span>
                        Base x difficulty x hint penalty
                    </div>
                    <div class="badge">
                        <span>Mastery logic</span>
                        Advance, stabilize, or review mode
                    </div>
                    <div class="badge">
                        <span>Timing signal</span>
                        Flags struggle when response time spikes
                    </div>
                    <div class="badge">
                        <span>Consistency scan</span>
                        Detects fluctuating answer patterns
                    </div>
                </div>
            </aside>
        </section>
    `);

    document.getElementById("register-form").addEventListener("submit", handleRegister);
}

async function handleRegister(event) {
    event.preventDefault();
    state.error = "";
    const form = new FormData(event.currentTarget);
    const payload = {
        name: String(form.get("name") || "").trim(),
        topic: String(form.get("topic") || "").trim(),
        educationLevel: String(form.get("educationLevel") || "").trim(),
    };

    if (!payload.name) {
        state.error = "Please add a learner name before starting.";
        renderOnboarding();
        return;
    }

    renderMessage("Creating learner profile and preparing the first adaptive quiz...");
    try {
        const snapshot = await api("/api/profile/register", {
            method: "POST",
            body: payload,
        });
        state.profileSnapshot = snapshot;
        state.activeTopic = payload.topic;
        localStorage.setItem(PROFILE_KEY, snapshot.profile.id);
        await startSession(payload.topic, payload.educationLevel);
    } catch (error) {
        state.error = error.message || "Unable to create the learner profile.";
        renderOnboarding();
    }
}

function renderDashboard() {
    const activeTopic = getPreferredTopic();
    state.activeTopic = activeTopic ? activeTopic.topic : state.activeTopic;
    const topicOptions = state.meta.topics
        .map((topic) => {
            const selected = activeTopic && activeTopic.topic === topic.id ? "selected" : "";
            return `<option value="${escapeHtml(topic.id)}" ${selected}>${escapeHtml(topic.label)}</option>`;
        })
        .join("");
    const levelOptions = state.meta.educationLevels
        .map((level) => {
            const selected = state.profileSnapshot.profile.educationLevel === level ? "selected" : "";
            return `<option value="${escapeHtml(level)}" ${selected}>${escapeHtml(level)}</option>`;
        })
        .join("");
    const history = renderHistory(state.profileSnapshot.recentSessions);

    renderShell(`
        <section class="hero">
            <div class="hero-copy">
                <h2>${escapeHtml(state.profileSnapshot.profile.name)}'s adaptive workspace</h2>
                <p>
                    The learner profile is saved, so every new session can adjust difficulty using prior mastery,
                    hints, response time, and inconsistency signals.
                </p>
            </div>
            <div class="hero-aside">
                <div class="mini-note">
                    <strong>Current track</strong>
                    ${activeTopic ? `${formatTopic(activeTopic.topic)} Â· ${capitalize(activeTopic.currentDifficulty)}` : "No topic selected yet"}
                </div>
                <div class="mini-note">
                    <strong>Sessions completed</strong>
                    ${activeTopic ? activeTopic.sessionsCompleted : 0}
                </div>
            </div>
        </section>
        <section class="dashboard-grid">
            <section class="panel">
                <h3>Start the next web session</h3>
                <form id="start-form" class="form-grid">
                    <div class="input-row">
                        <label for="topic">Topic</label>
                        <select id="topic" name="topic">${topicOptions}</select>
                    </div>
                    <div class="input-row">
                        <label for="educationLevel">Education level</label>
                        <select id="educationLevel" name="educationLevel">${levelOptions}</select>
                    </div>
                    <div class="button-row">
                        <button class="button" type="submit">Start adaptive assessment</button>
                        <button class="ghost-button" type="button" id="reset-profile">Reset learner</button>
                    </div>
                </form>
            </section>
            <aside class="panel">
                <h3>Profile signals</h3>
                ${activeTopic ? `
                    <div class="topic-card">
                        <div class="topic-title">
                            <strong>${formatTopic(activeTopic.topic)}</strong>
                            <span class="chip">${capitalize(activeTopic.predictedBand)}</span>
                        </div>
                        <p class="small-copy">Difficulty: ${capitalize(activeTopic.currentDifficulty)} Â· Last decision: ${capitalize(activeTopic.lastDecision)}</p>
                        <div class="metric-grid">
                            <div class="metric-card">
                                <span>Mastery</span>
                                <strong>${formatPercent(activeTopic.mastery)}</strong>
                            </div>
                            <div class="metric-card">
                                <span>Avg response</span>
                                <strong>${formatSeconds(activeTopic.avgResponseTime)}</strong>
                            </div>
                            <div class="metric-card">
                                <span>Inconsistency</span>
                                <strong>${formatIndex(activeTopic.inconsistencyScore)}</strong>
                            </div>
                        </div>
                    </div>
                ` : '<p class="muted-copy">Start a topic to build the first adaptive profile.</p>'}
            </aside>
        </section>
        <section class="panel">
            <h3>Recent saved sessions</h3>
            ${history}
        </section>
    `);

    document.getElementById("start-form").addEventListener("submit", handleStartFromDashboard);
    document.getElementById("reset-profile").addEventListener("click", resetProfile);
}

async function handleStartFromDashboard(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await startSession(String(form.get("topic")), String(form.get("educationLevel")));
}

async function startSession(topic, educationLevel) {
    renderMessage("Generating a personalized quiz and tuning the first difficulty band...");
    const response = await api("/api/session/start", {
        method: "POST",
        body: {
            profileId: state.profileSnapshot.profile.id,
            topic,
            educationLevel,
            questionCount: 5,
        },
    });
    state.session = response;
    state.activeTopic = topic;
    state.answers = {};
    state.currentQuestionIndex = 0;
    state.questionStartedAt = performance.now();
    renderQuiz();
}

function renderQuiz() {
    const question = getCurrentQuestion();
    if (!question) {
        renderDashboard();
        return;
    }

    const answer = getAnswer(question.id);
    const progress = ((state.currentQuestionIndex + 1) / state.session.questions.length) * 100;
    const options = question.options
        .map((option, index) => `
            <button class="option-button ${answer.selectedIndex === index ? "active" : ""}" data-option-index="${index}" type="button">
                <span class="option-label">${String.fromCharCode(65 + index)}</span>
                ${escapeHtml(option)}
            </button>
        `)
        .join("");
    const revealedHints = question.hints
        .slice(0, answer.hintsUsed)
        .map((hint) => `<div class="hint-card">${escapeHtml(hint)}</div>`)
        .join("");
    const hintButton = answer.hintsUsed < question.hints.length
        ? `<button class="hint-button" id="show-hint" type="button">Reveal hint ${answer.hintsUsed + 1}</button>`
        : "";

    renderShell(`
        <section class="question-shell">
            <div class="question-top">
                <div>
                    <p class="eyebrow">Question ${state.currentQuestionIndex + 1} of ${state.session.questions.length}</p>
                    <h2>${escapeHtml(state.session.quizTitle)}</h2>
                </div>
                <div class="chip">${capitalize(question.difficulty)} Â· ${escapeHtml(question.skillTag)}</div>
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:${progress}%"></div>
            </div>
            <p class="question-prompt">${escapeHtml(question.prompt)}</p>
            <div class="options-grid">${options}</div>
            <div class="hint-area">
                ${hintButton}
                ${revealedHints}
            </div>
            <div class="button-row">
                <button class="button" id="next-question" type="button">
                    ${state.currentQuestionIndex === state.session.questions.length - 1 ? "Finish assessment" : "Save and continue"}
                </button>
                <button class="ghost-button" id="stop-session" type="button">Stop and return</button>
            </div>
            ${state.error ? `<div class="error-box">${escapeHtml(state.error)}</div>` : ""}
        </section>
    `);

    document.querySelectorAll("[data-option-index]").forEach((button) => {
        button.addEventListener("click", () => {
            answer.selectedIndex = Number(button.dataset.optionIndex);
            state.error = "";
            renderQuiz();
        });
    });

    const hintControl = document.getElementById("show-hint");
    if (hintControl) {
        hintControl.addEventListener("click", () => {
            answer.hintsUsed += 1;
            renderQuiz();
        });
    }

    document.getElementById("next-question").addEventListener("click", moveToNextQuestion);
    document.getElementById("stop-session").addEventListener("click", renderDashboard);
}

async function moveToNextQuestion() {
    const question = getCurrentQuestion();
    const answer = getAnswer(question.id);
    if (answer.selectedIndex === null || answer.selectedIndex === undefined) {
        state.error = "Pick an answer before continuing so the evaluation stays complete.";
        renderQuiz();
        return;
    }

    answer.responseTimeSec = elapsedSeconds();
    state.error = "";

    if (state.currentQuestionIndex < state.session.questions.length - 1) {
        state.currentQuestionIndex += 1;
        state.questionStartedAt = performance.now();
        renderQuiz();
        return;
    }

    renderMessage("Scoring the session, updating mastery, and saving the learner profile...");
    const answers = state.session.questions.map((item) => ({
        questionId: item.id,
        selectedIndex: getAnswer(item.id).selectedIndex,
        hintsUsed: getAnswer(item.id).hintsUsed,
        responseTimeSec: getAnswer(item.id).responseTimeSec,
    }));

    const result = await api("/api/session/submit", {
        method: "POST",
        body: {
            sessionId: state.session.sessionId,
            answers,
        },
    });
    state.profileSnapshot = result.profileSnapshot;
    state.session.result = result.evaluation;
    renderResults();
}

function renderResults() {
    const evaluation = state.session.result;
    const activeTopic = getPreferredTopic();
    const reviews = evaluation.questionReviews
        .map((review) => `
            <article class="detail-card ${review.isCorrect ? "correct" : "missed"}">
                <div class="detail-head">
                    <strong>${escapeHtml(review.prompt)}</strong>
                    <span class="chip">${review.isCorrect ? "Correct" : "Review needed"}</span>
                </div>
                <div class="detail-meta">
                    <span class="tiny-pill">${capitalize(review.difficulty)}</span>
                    <span class="tiny-pill">${escapeHtml(review.skillTag)}</span>
                    <span class="tiny-pill">${review.hintsUsed} hint${review.hintsUsed === 1 ? "" : "s"}</span>
                    <span class="tiny-pill">${formatSeconds(review.responseTimeSec)}</span>
                </div>
                <p class="small-copy"><strong>Your answer:</strong> ${escapeHtml(review.selectedText || "No answer")}</p>
                <p class="small-copy"><strong>Correct answer:</strong> ${escapeHtml(review.correctText || "Unavailable")}</p>
                <p class="small-copy"><strong>Explanation:</strong> ${escapeHtml(review.explanation)}</p>
                <p class="small-copy"><strong>Weighted contribution:</strong> ${review.weightedScore}</p>
            </article>
        `)
        .join("");

    renderShell(`
        <section class="results-shell">
            <div class="question-top">
                <div>
                    <p class="eyebrow">Session saved</p>
                    <h2>${escapeHtml(evaluation.prediction.headline)}</h2>
                </div>
                <div class="chip">${escapeHtml(evaluation.prediction.band)}</div>
            </div>
            <p class="status-copy">${escapeHtml(evaluation.summary)}</p>
            <div class="metric-grid">
                <div class="metric-card">
                    <span>Mastery</span>
                    <strong>${formatPercent(evaluation.masteryPercent)}</strong>
                </div>
                <div class="metric-card">
                    <span>Accuracy</span>
                    <strong>${formatPercent(evaluation.accuracyPercent)}</strong>
                </div>
                <div class="metric-card">
                    <span>Weighted score</span>
                    <strong>${evaluation.rawScore}</strong>
                </div>
                <div class="metric-card">
                    <span>Avg response</span>
                    <strong>${formatSeconds(evaluation.averageResponseTimeSec)}</strong>
                </div>
                <div class="metric-card">
                    <span>Suspicion level</span>
                    <strong>${escapeHtml(evaluation.suspicionLevel)}</strong>
                </div>
                <div class="metric-card">
                    <span>Next mode</span>
                    <strong>${capitalize(evaluation.decision.mode)}</strong>
                </div>
            </div>
        </section>
        <section class="results-grid">
            <section class="panel">
                <h3>Question-by-question explanation</h3>
                <div class="session-detail">${reviews}</div>
            </section>
            <aside class="panel">
                <h3>Overall evaluation</h3>
                <div class="result-callout">
                    <strong>${escapeHtml(evaluation.decision.recommendation)}</strong>
                    <p class="small-copy">${escapeHtml(evaluation.decision.rationale)}</p>
                </div>
                <div class="result-callout">
                    <strong>Prediction</strong>
                    <p class="small-copy">${escapeHtml(evaluation.prediction.detail)}</p>
                </div>
                <div class="result-callout">
                    <strong>Focus skills</strong>
                    <p class="small-copy">${escapeHtml((evaluation.focusSkills || []).join(", ") || "No major weak spots were detected in this session.")}</p>
                </div>
                ${activeTopic ? `
                    <div class="result-callout">
                        <strong>Saved profile</strong>
                        <p class="small-copy">
                            ${formatTopic(activeTopic.topic)} is now set to ${capitalize(activeTopic.currentDifficulty)}
                            difficulty with ${formatPercent(activeTopic.mastery)} rolling mastery.
                        </p>
                    </div>
                ` : ""}
                <div class="button-row">
                    <button class="button" id="new-session" type="button">Start another session</button>
                    <button class="ghost-button" id="back-dashboard" type="button">Back to dashboard</button>
                </div>
            </aside>
        </section>
        <section class="panel">
            <h3>Recent history</h3>
            ${renderHistory(state.profileSnapshot.recentSessions)}
        </section>
    `);

    document.getElementById("new-session").addEventListener("click", () => {
        if (!activeTopic) {
            renderDashboard();
            return;
        }
        startSession(activeTopic.topic, activeTopic.educationLevel).catch((error) => {
            state.error = error.message || "Unable to start the next session.";
            renderDashboard();
        });
    });
    document.getElementById("back-dashboard").addEventListener("click", renderDashboard);
}

function renderHistory(sessions) {
    if (!sessions || !sessions.length) {
        return '<div class="empty-state">No completed sessions yet. The first assessment will appear here.</div>';
    }

    return sessions
        .map((session) => `
            <div class="history-card">
                <strong>${formatTopic(session.topic)} Â· ${capitalize(session.deliveredDifficulty)}</strong>
                <p class="small-copy">
                    ${formatDate(session.completedAt || session.createdAt)} Â· ${escapeHtml(session.predictionBand || "Building")}
                </p>
                <div class="history-bar">
                    <span style="width:${Math.min(100, Number(session.masteryPercent || 0))}%"></span>
                </div>
                <p class="small-copy">Mastery: ${formatPercent(session.masteryPercent || 0)} Â· Mode: ${capitalize(session.mode || "new")}</p>
            </div>
        `)
        .join("");
}

function getCurrentQuestion() {
    return state.session?.questions?.[state.currentQuestionIndex] || null;
}

function getAnswer(questionId) {
    if (!state.answers[questionId]) {
        state.answers[questionId] = {
            questionId,
            selectedIndex: null,
            hintsUsed: 0,
            responseTimeSec: 0,
        };
    }
    return state.answers[questionId];
}

function getPreferredTopic() {
    const topics = state.profileSnapshot?.topics || [];
    if (!topics.length) {
        return null;
    }
    return topics.find((item) => item.topic === state.activeTopic) || topics[0];
}

function resetProfile() {
    localStorage.removeItem(PROFILE_KEY);
    state.profileSnapshot = null;
    state.activeTopic = null;
    state.session = null;
    state.answers = {};
    state.error = "";
    renderOnboarding();
}

function elapsedSeconds() {
    const elapsedMs = performance.now() - state.questionStartedAt;
    return Math.max(1, Math.round(elapsedMs / 100) / 10);
}

function renderShell(content) {
    document.getElementById("app").innerHTML = content;
}

async function api(path, options = {}) {
    const requestOptions = {
        method: options.method || "GET",
        headers: {
            "Content-Type": "application/json",
        },
    };
    if (options.body) {
        requestOptions.body = JSON.stringify(options.body);
    }

    const response = await fetch(path, requestOptions);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.error || "Request failed");
    }
    return data;
}

function formatTopic(topicId) {
    const topic = state.meta.topics.find((item) => item.id === topicId);
    return topic ? topic.label : capitalize(topicId);
}

function formatPercent(value) {
    return `${Number(value || 0).toFixed(1)}%`;
}

function formatSeconds(value) {
    return `${Number(value || 0).toFixed(1)}s`;
}

function formatIndex(value) {
    return Number(value || 0).toFixed(2);
}

function formatDate(value) {
    if (!value) {
        return "Saved";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

function capitalize(value) {
    if (!value) {
        return "";
    }
    const text = String(value);
    return text.charAt(0).toUpperCase() + text.slice(1);
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}
