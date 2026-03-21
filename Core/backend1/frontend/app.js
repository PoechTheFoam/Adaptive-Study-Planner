const state = {
    userId: null,
    currentQuestion: null,
    hintsUsed: 0,
    timerStartedAt: null,
    timerHandle: null,
};

const els = {
    healthStatus: document.getElementById("healthStatus"),
    healthDetail: document.getElementById("healthDetail"),
    sessionState: document.getElementById("sessionState"),
    sessionDetail: document.getElementById("sessionDetail"),
    userForm: document.getElementById("userForm"),
    createUserBtn: document.getElementById("createUserBtn"),
    questionBtn: document.getElementById("questionBtn"),
    hintBtn: document.getElementById("hintBtn"),
    submitBtn: document.getElementById("submitBtn"),
    nextBtn: document.getElementById("nextBtn"),
    refreshProgressBtn: document.getElementById("refreshProgressBtn"),
    topicSelect: document.getElementById("topicSelect"),
    userSummary: document.getElementById("userSummary"),
    topicBadge: document.getElementById("topicBadge"),
    difficultyBadge: document.getElementById("difficultyBadge"),
    timerBadge: document.getElementById("timerBadge"),
    questionText: document.getElementById("questionText"),
    hintList: document.getElementById("hintList"),
    answerInput: document.getElementById("answerInput"),
    feedbackBox: document.getElementById("feedbackBox"),
    nextActionBox: document.getElementById("nextActionBox"),
    profileGrid: document.getElementById("profileGrid"),
    progressGrid: document.getElementById("progressGrid"),
};

async function api(path, options = {}) {
    const response = await fetch(path, {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
        ...options,
    });

    if (!response.ok) {
        let message = `Request failed (${response.status})`;
        try {
            const data = await response.json();
            message = data.detail || JSON.stringify(data);
        } catch (error) {
            message = await response.text();
        }
        throw new Error(message);
    }

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        return response.json();
    }
    return response.text();
}

function setHealth(status, detail, good = true) {
    els.healthStatus.textContent = status;
    els.healthDetail.textContent = detail;
    els.healthStatus.style.color = good ? "var(--success)" : "var(--danger)";
}

function setSessionState(status, detail) {
    els.sessionState.textContent = status;
    els.sessionDetail.textContent = detail;
}

function startTimer() {
    stopTimer();
    state.timerStartedAt = performance.now();
    els.timerBadge.textContent = "00.0s";
    state.timerHandle = window.setInterval(() => {
        if (!state.timerStartedAt) {
            return;
        }
        const elapsedSeconds =
            (performance.now() - state.timerStartedAt) / 1000;
        els.timerBadge.textContent = `${elapsedSeconds.toFixed(1)}s`;
    }, 100);
}

function stopTimer() {
    if (state.timerHandle) {
        window.clearInterval(state.timerHandle);
        state.timerHandle = null;
    }
}

function getElapsedSeconds() {
    if (!state.timerStartedAt) {
        return 0;
    }
    return Number(((performance.now() - state.timerStartedAt) / 1000).toFixed(2));
}

function resetQuestionState() {
    state.currentQuestion = null;
    state.hintsUsed = 0;
    state.timerStartedAt = null;
    stopTimer();
    els.hintBtn.disabled = true;
    els.submitBtn.disabled = true;
    els.nextBtn.disabled = true;
    els.questionText.textContent = "Fetch a question to begin.";
    els.topicBadge.textContent = "No topic";
    els.difficultyBadge.textContent = "No difficulty";
    els.timerBadge.textContent = "00.0s";
    els.hintList.innerHTML = "";
    els.answerInput.value = "";
}

function setFeedback(message, tone = "neutral") {
    els.feedbackBox.className = `feedback-box ${tone}`;
    els.feedbackBox.textContent = message;
}

function renderUserSummary(profile) {
    els.userSummary.className = "feedback-box neutral";
    els.userSummary.innerHTML = [
        `<strong>${profile.name}</strong>`,
        `Learner ID: ${profile.user_id}`,
        `Skill: ${profile.skill_level}`,
        `Goal: ${profile.goal}`,
        `Topic: ${profile.current_topic}`,
        `Difficulty: ${profile.current_difficulty}`,
    ].join("<br>");
}

function renderProfile(profile) {
    els.profileGrid.innerHTML = `
        <div class="stat-card">
            <span>Learner</span>
            <strong>${profile.name}</strong>
        </div>
        <div class="stat-card">
            <span>Topic</span>
            <strong>${profile.current_topic}</strong>
        </div>
        <div class="stat-card">
            <span>Difficulty</span>
            <strong>${profile.current_difficulty}</strong>
        </div>
        <div class="stat-card">
            <span>Mastery</span>
            <strong>${Number(profile.overall_mastery).toFixed(1)}%</strong>
        </div>
    `;
}

function renderProgress(progress) {
    if (!progress.topics.length) {
        els.progressGrid.innerHTML = `
            <div class="empty-state">
                Progress cards will appear once the learner starts answering questions.
            </div>
        `;
        return;
    }

    els.progressGrid.innerHTML = progress.topics
        .map(
            (topic) => `
                <article class="progress-card">
                    <span>${topic.topic}</span>
                    <strong>${topic.mastery_score} mastery</strong>
                    <p>${topic.accuracy} accuracy</p>
                    <p>${topic.average_response_time} avg response time</p>
                    <p>${topic.confidence_level} confidence</p>
                </article>
            `
        )
        .join("");
}

function renderQuestion(question) {
    state.currentQuestion = question;
    state.hintsUsed = 0;
    els.topicBadge.textContent = question.topic;
    els.difficultyBadge.textContent = question.difficulty;
    els.questionText.textContent = question.question;
    els.hintList.innerHTML = "";
    els.answerInput.value = "";
    els.hintBtn.disabled = false;
    els.submitBtn.disabled = false;
    els.nextBtn.disabled = true;
    setFeedback("Question loaded. When you are ready, answer it below.", "neutral");
    startTimer();
}

function renderHints(hint) {
    const wrapper = document.createElement("div");
    wrapper.className = "hint-item";
    wrapper.innerHTML = `<strong>Hint ${hint.hint_number}</strong>${hint.hint}`;
    els.hintList.appendChild(wrapper);
}

function renderNextAction(decision) {
    els.nextActionBox.className = "feedback-box neutral";
    els.nextActionBox.innerHTML = [
        `<strong>${decision.action}</strong>`,
        `Recommended topic: ${decision.recommended_topic}`,
        `Recommended difficulty: ${decision.recommended_difficulty}`,
        `Reason: ${decision.reason}`,
        `Feedback: ${decision.feedback}`,
    ].join("<br>");
}

async function refreshProfileAndProgress() {
    if (!state.userId) {
        return;
    }

    const [profile, progress] = await Promise.all([
        api(`/user/profile?user_id=${encodeURIComponent(state.userId)}`),
        api(`/user/progress?user_id=${encodeURIComponent(state.userId)}`),
    ]);

    renderUserSummary(profile);
    renderProfile(profile);
    renderProgress(progress);
    setSessionState(
        "Learner active",
        `${profile.name} is on ${profile.current_topic} (${profile.current_difficulty})`
    );
}

async function loadTopics() {
    const topicsResponse = await api("/topics");
    els.topicSelect.innerHTML = topicsResponse.topics
        .map((topic) => `<option value="${topic}">${topic}</option>`)
        .join("");
}

async function checkHealth() {
    try {
        const health = await api("/health");
        setHealth("Connected", health.message, true);
    } catch (error) {
        setHealth("Offline", error.message, false);
        setFeedback(
            "Backend is not reachable yet. Start FastAPI and refresh this page.",
            "error"
        );
    }
}

async function createUser() {
    const formData = new FormData(els.userForm);
    const payload = Object.fromEntries(formData.entries());

    const profile = await api("/user/create", {
        method: "POST",
        body: JSON.stringify(payload),
    });

    state.userId = profile.user_id;
    resetQuestionState();
    renderUserSummary(profile);
    renderProfile(profile);
    renderProgress({ topics: [] });
    setSessionState(
        "Learner active",
        `${profile.name} starts on ${profile.current_topic}`
    );
    els.refreshProgressBtn.disabled = false;
    await loadQuestion();
}

async function loadQuestion() {
    if (!state.userId) {
        throw new Error("Create a learner first.");
    }

    const question = await api("/get_question", {
        method: "POST",
        body: JSON.stringify({ user_id: state.userId }),
    });

    renderQuestion(question);
    await refreshProfileAndProgress();
}

async function requestHint() {
    if (!state.userId || !state.currentQuestion) {
        throw new Error("Load a question before requesting a hint.");
    }

    const nextHintNumber = state.hintsUsed + 1;
    const hint = await api(
        `/get_hint?user_id=${encodeURIComponent(state.userId)}&exercise_id=${encodeURIComponent(
            state.currentQuestion.exercise_id
        )}&hint_number=${nextHintNumber}`,
        { method: "POST" }
    );

    state.hintsUsed = hint.hint_number;
    renderHints(hint);

    if (state.hintsUsed >= 2) {
        els.hintBtn.disabled = true;
    }
}

async function submitAnswer() {
    if (!state.userId || !state.currentQuestion) {
        throw new Error("Load a question before submitting an answer.");
    }

    const answer = els.answerInput.value.trim();
    if (!answer) {
        throw new Error("Enter an answer before submitting.");
    }

    const result = await api("/submit_answer", {
        method: "POST",
        body: JSON.stringify({
            user_id: state.userId,
            exercise_id: state.currentQuestion.exercise_id,
            user_answer: answer,
            response_time: getElapsedSeconds(),
            hints_used: state.hintsUsed,
        }),
    });

    stopTimer();
    setFeedback(
        `${result.feedback}\n\nExplanation: ${result.explanation}\n\nMastery: ${Number(
            result.mastery_score
        ).toFixed(1)}%`,
        result.is_correct ? "success" : "error"
    );

    const decision = await api(
        `/next_action?user_id=${encodeURIComponent(state.userId)}`,
        { method: "POST" }
    );
    renderNextAction(decision);
    els.nextBtn.disabled = false;
    els.hintBtn.disabled = true;
    els.submitBtn.disabled = true;
    await refreshProfileAndProgress();
}

async function runAction(action) {
    try {
        await action();
    } catch (error) {
        setFeedback(error.message, "error");
    }
}

els.createUserBtn.addEventListener("click", () => runAction(createUser));
els.questionBtn.addEventListener("click", () => runAction(loadQuestion));
els.hintBtn.addEventListener("click", () => runAction(requestHint));
els.submitBtn.addEventListener("click", () => runAction(submitAnswer));
els.nextBtn.addEventListener("click", () => runAction(loadQuestion));
els.refreshProgressBtn.addEventListener("click", () => runAction(refreshProfileAndProgress));

window.addEventListener("load", async () => {
    resetQuestionState();
    await Promise.all([checkHealth(), loadTopics()]);
});
