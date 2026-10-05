// Dynamic Runbook Step Form Handler & AI Generator

document.addEventListener('DOMContentLoaded', function () {
    const stepsContainer = document.getElementById('steps-container');
    const addStepBtn = document.getElementById('add-step-btn');
    const runbookForm = document.getElementById('runbook-form');
    const stepsJsonInput = document.getElementById('steps_json');

    // Initialize or re-index step numbers
    function reindexSteps() {
        const stepCards = stepsContainer.querySelectorAll('.step-card');
        stepCards.forEach((card, index) => {
            const stepNum = index + 1;
            const badge = card.querySelector('.step-order-badge');
            if (badge) badge.innerText = `Step ${stepNum}`;
            
            // Show/hide remove button if only 1 step
            const removeBtn = card.querySelector('.btn-remove-step');
            if (removeBtn) {
                removeBtn.style.display = stepCards.length > 1 ? 'inline-block' : 'none';
            }
        });
    }

    // Function to add a new step card
    window.addStepCard = function (stepData = {}) {
        const index = stepsContainer.querySelectorAll('.step-card').length;
        const card = document.createElement('div');
        card.className = 'step-card card-devops p-3 mb-3 border-secondary';
        card.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom border-secondary">
                <span class="step-order-badge badge bg-indigo-subtle text-indigo border border-indigo-subtle px-2 py-1">Step ${index + 1}</span>
                <button type="button" class="btn btn-sm btn-outline-danger btn-remove-step">
                    <i class="bi bi-trash"></i> Remove
                </button>
            </div>
            <div class="mb-3">
                <label class="form-label">Step Title</label>
                <input type="text" class="form-control form-control-devops step-title-input" 
                    placeholder="e.g. Verify Database Connections" value="${stepData.title || ''}" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Instructions / Commands</label>
                <textarea class="form-control form-control-devops font-monospace step-instructions-input" 
                    rows="3" placeholder="Enter shell commands, SQL queries, or manual instructions..." required>${stepData.instructions || ''}</textarea>
            </div>
            <div>
                <label class="form-label">Expected Outcome</label>
                <input type="text" class="form-control form-control-devops step-expected-input" 
                    placeholder="e.g. Connection count drops below 50" value="${stepData.expectedOutcome || stepData.expected_outcome || ''}">
            </div>
        `;

        card.querySelector('.btn-remove-step').addEventListener('click', function () {
            card.remove();
            reindexSteps();
        });

        stepsContainer.appendChild(card);
        reindexSteps();
    };

    if (addStepBtn) {
        addStepBtn.addEventListener('click', function () {
            window.addStepCard();
        });
    }

    // Delegate remove step button clicks for pre-rendered steps
    if (stepsContainer) {
        stepsContainer.addEventListener('click', function (e) {
            if (e.target.closest('.btn-remove-step')) {
                const card = e.target.closest('.step-card');
                if (card && stepsContainer.querySelectorAll('.step-card').length > 1) {
                    card.remove();
                    reindexSteps();
                }
            }
        });
    }

    // Form submission: serialize steps to JSON
    if (runbookForm) {
        runbookForm.addEventListener('submit', function (e) {
            const steps = [];
            const stepCards = stepsContainer.querySelectorAll('.step-card');

            stepCards.forEach((card, index) => {
                const title = card.querySelector('.step-title-input').value.trim();
                const instructions = card.querySelector('.step-instructions-input').value.trim();
                const expectedOutcome = card.querySelector('.step-expected-input').value.trim();

                if (title && instructions) {
                    steps.push({
                        order: index + 1,
                        title: title,
                        instructions: instructions,
                        expectedOutcome: expectedOutcome
                    });
                }
            });

            if (steps.length === 0) {
                e.preventDefault();
                showToast('Please provide at least one valid step with instructions.', 'danger');
                return false;
            }

            if (stepsJsonInput) {
                stepsJsonInput.value = JSON.stringify(steps);
            }
        });
    }

    // ==========================================
    // GROQ AI GENERATION HANDLER
    // ==========================================
    const aiModalEl = document.getElementById('groqAiGeneratorModal');
    const aiPromptInput = document.getElementById('ai-prompt-input');
    const generateAiBtn = document.getElementById('btn-execute-ai-generation');
    const aiLoadingSpinner = document.getElementById('ai-generation-spinner');
    const aiErrorAlert = document.getElementById('ai-generation-error');

    if (generateAiBtn) {
        generateAiBtn.addEventListener('click', async function () {
            const prompt = aiPromptInput.value.trim();
            if (!prompt) {
                aiErrorAlert.innerText = 'Please describe the incident or task you want to generate.';
                aiErrorAlert.classList.remove('d-none');
                return;
            }

            aiErrorAlert.classList.add('d-none');
            aiLoadingSpinner.classList.remove('d-none');
            generateAiBtn.disabled = true;

            try {
                const response = await apiRequest('/api/ai/generate-runbook', {
                    method: 'POST',
                    body: { prompt: prompt }
                });

                if (response.success && response.data) {
                    const data = response.data;
                    
                    // Populate Form Fields
                    const titleField = document.getElementById('title');
                    const descField = document.getElementById('description');
                    if (titleField && data.title) titleField.value = data.title;
                    if (descField && data.description) descField.value = data.description;

                    // Populate Steps
                    if (Array.isArray(data.steps) && data.steps.length > 0) {
                        stepsContainer.innerHTML = '';
                        data.steps.forEach(s => window.addStepCard(s));
                    }

                    // Close modal and show toast
                    const bsModal = bootstrap.Modal.getInstance(aiModalEl);
                    if (bsModal) bsModal.hide();
                    showToast('Runbook successfully drafted with Groq Llama model!', 'success');
                } else {
                    throw new Error(response.message || 'Failed to generate runbook');
                }
            } catch (err) {
                aiErrorAlert.innerText = err.message || 'Error communicating with Groq API';
                aiErrorAlert.classList.remove('d-none');
            } finally {
                aiLoadingSpinner.classList.add('d-none');
                generateAiBtn.disabled = false;
            }
        });
    }
});
